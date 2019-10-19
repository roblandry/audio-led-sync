#!/usr/bin/env python3
""" Audio pitch/volume to light color/brightness.

    Author: Rob Landry (rob.a.landry@gmail.com)"""
import os
import sys
import contextlib
import time
import requests
import json
import argparse

# For Music
# import alsaaudio as aa
import pyaudio
import aubio
import numpy as np
import colorsys
import webcolors

# For NeoPixel
from neopixel import *

SLEEP = 0.5

# AUDIO CONFIGURATION
#
# FORMAT = pyaudio.paInt16
# CHANNELS =
# RATE =
# CHUNK =
# DEVICE_INDEX =
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 16000
CHUNK = 1024
DEVICE_INDEX = 0

# LED STRIP CONFIGURATION
# LED_COUNT      = 10        # Number of LED pixels.
# LED_PIN        = 18          # GPIO pin connected to the pixels (18 uses PWM!).
# LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
# LED_DMA        = 10          # DMA channel to use for generating signal (try 10)
# LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
# LED_INVERT     = False    # True to invert the signal (when using NPN transistor level shift)
# LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_COUNT = 10
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0

# HASS CONFIGURATION
# HASS_URL = "http://192.168.1.X:8123"
# HASS_PASS = "API TOKEN"
HASS_URL = "http://IP:8123"
HASS_PASS = (
    "API"
    "KEY"
    "HERE"
)
COLOR_LIGHTS = "light.living_room, light.garden_lights"
WHITE_LIGHTS = ""

# prevents same colors repeating by changing hs +/- 30
PREVENT_STATIC = False


@contextlib.contextmanager
def silence():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)


def get_colour_name(rgb_triplet):
    min_colours = {}
    for key, name in webcolors.css21_hex_to_names.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - rgb_triplet[0]) ** 2
        gd = (g_c - rgb_triplet[1]) ** 2
        bd = (b_c - rgb_triplet[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]


# pylint: disable=undefined-variable
class ProcessColor:
    """ Docstring. """

    def __init__(self, **kwargs):
        """ Docstring. """
        self.color = 0
        self.kwargs = kwargs
        with silence():
            self.audioSync()

    def audioSync(self):  # pylint: disable=too-many-locals
        """ Docstring. """

        hassSync = self.kwargs.get("hass")
        ledSync = self.kwargs.get("led")

        p = pyaudio.PyAudio()

        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            input_device_index=DEVICE_INDEX,
        )

        # aubio pitch detection
        pDetection = aubio.pitch("default", 2048, 2048 // 2, 16000)
        pDetection.set_unit("Hz")
        pDetection.set_silence(-40)

        print("Audio Controlled LEDs.")

        while True:
            # Read data from device
            if stream.is_stopped():
                stream.start_stream()
            data = stream.read(CHUNK)
            stream.stop_stream()

            # determine pitch
            samples = np.fromstring(data, dtype=aubio.float_type)
            pitch = pDetection(samples)[0]
            # print(pitch)

            # determine volume
            volume = np.sum(samples ** 2) / len(samples)
            volume = "{:.6f}".format(volume)
            # print(volume)

            # calculate a brightness based on volume level
            brightness = self.calc_bright(volume)

            # get color based on pitch
            hs_color = self.calc_hs(pitch)
            if PREVENT_STATIC:
                if (self.color <= (hs_color + 5) and self.color >= (hs_color - 5)):
                    if int(hs_color) <= 30:
                        hs_color = hs_color + 30
                    else:
                        hs_color = hs_color - 30
            self.color = hs_color
            
            # print(self.color)
            rgb_color = self.hs_to_rbg(hs_color)
            r, g, b = rgb_color

            # output something to console
            print(get_colour_name(rgb_color))
            print("HS Color: %s" % hs_color)
            print("RGB Color: (%s, %s, %s)" % rgb_color)
            print("Brightness: %s\n" % brightness)

            # For NeoPixels
            if ledSync:
                neoPixelStrip(rgb_color=(r, g, b), brightness=brightness)

            # For HASS Lights
            if hassSync:
                self.exec_hass(hs_color, brightness)

            time.sleep(SLEEP)

        stream.stop_stream()
        stream.close()

    def calc_hs(self, pitch):
        """ calculate the hs color based off max of 500Hz? thats about the highest ive seen. """
        hs_color = pitch / 500
        hs_color = hs_color * 360
        if hs_color > 360:
            hs_color = 360
        return hs_color

    def hs_to_rbg(self, hs_color):
        """ Get RGB color from HS. """
        r, g, b = colorsys.hsv_to_rgb(hs_color / 360.0, 1, 1)
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        rgb_color = (r, g, b)
        return rgb_color

    def calc_bright(self, brightness):
        """ calculate a brightness based on volume level. """
        brightness = int(float(brightness) * 100)
        if brightness < 10:
            brightness = 10
        return brightness

    def exec_hass(self, hs_color=0, brightness=100):
        saturation = 100
        if hs_color is 0:
            saturation = 0

        url = "/api/services/light/turn_on"

        # color lights
        payload = {
            "entity_id": COLOR_LIGHTS,
            "hs_color": [int(hs_color), saturation],
            "brightness_pct": brightness,
            "transition": 0.5,
        }

        hassConn(url=url, payload=payload)


class hassConn:
    """ Format request to HASS. """

    def __init__(self, **kwargs):
        """ Initialize the Class. """
        self._url = None
        self._headers = None
        self._payload = None

        if "url" in kwargs:
            self._url = kwargs.get("url")
        if "headers" in kwargs:
            self._headers = kwargs.get("headers")
        if "payload" in kwargs:
            self._payload = kwargs.get("payload")

        self.setUrl(self._url)
        self.setHeaders(self._headers)
        self.setPayload(self._payload)

        if kwargs.get("theType") == "GET":
            self.get()
        else:
            self.post()

    def setUrl(self, url):
        """ Assign URL to var.

        Format: '/api/services/light/turn_on' """
        self._url = HASS_URL + url

    def setHeaders(self, headers):
        """ Assign header var. """
        if not headers:
            headers = {
                "Authorization": "Bearer " + HASS_PASS,
                "content-type": "application/json"
                }
        self._headers = headers

    def setPayload(self, payload):
        """ Verify payload is valid JSON and assign to var. """
        try:
            json.loads(json.dumps(payload))
        except ValueError:
            print("Invalid JSON!")
        self._payload = payload

    def post(self):
        """ POST the request. """
        response = requests.post(self._url, json=self._payload, headers=self._headers)
        if response.status_code != 200:
            print(response.text)

    def get(self):
        """ GET the request. """
        try:
            response = requests.get(self._url, headers=self._headers)
            response.raise_for_status()
            # print(response.text)
        except requests.exceptions.HTTPError as err:
            print("HTTP Error")
            print(err)
            exit()
            return "exception"

        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            print("Connection Timeout!")
            exit()
            return "exception"

        except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
            print("Too Many Redirects!")
            exit()
            return "exception"

        except requests.exceptions.RequestException as e:
            # catastrophic error. bail.
            print("Request Exception!")
            print(e)
            return "exception"
            # exit()    

        return response


# pylint: disable=undefined-variable
class neoPixelStrip:
    """ NeoPixel library strandtest example.

        Author: Tony DiCola (tony@tonydicola.com)
        Direct port of the Arduino NeoPixel library strandtest example.  Showcases
        various animations on a strip of NeoPixels.
    """

    def __init__(self, **kwargs):
        """ Create NeoPixel object with appropriate configuration. """
        self.strip = Adafruit_NeoPixel(
            LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL
        )

        self.function = kwargs.get("function")
        self.color = kwargs.get("color")
        self.wait_ms = kwargs.get("wait_ms")
        self.iterations = kwargs.get("iterations")
        self.entity = kwargs.get("entity")
        self.rgb_color = kwargs.get("rgb_color")
        self.brightness = kwargs.get("brightness")

        if self.rgb_color or self.brightness:
            self.audioColor()
        else:
            self.execDemos()

    def audioColor(self):
        r, g, b = self.rgb_color

        self.strip.begin()
        self.clearPixels()
        for i in range(self.strip.numPixels()):
            self.strip.setBrightness(self.brightness)
            self.strip.setPixelColor(i, Color(g, r, b))
            self.strip.show()

    def execDemos(self):
        self.strip.begin()
        self.clearPixels()
        if self.function in ("colorWipe", "allDemo"):
            self.doColor()
        elif self.function in ("theaterChase", "allDemo"):
            self.doTheater()
        elif self.function in ("rainbowCycle", "allDemo"):
            self.doRainbow()
        elif self.function is "hassEntity":
            self.doHass()
        elif self.function is "clear":
            self.clearPixels()

    def doColor(self):
        print("Color wipe animations.")
        if self.color or self.wait_ms:
            self.colorWipe(self.color, self.wait_ms)
        else:
            self.colorWipe(Color(255, 0, 0))  # Red wipe
            self.colorWipe(Color(0, 255, 0))  # Blue wipe
            self.colorWipe(Color(0, 0, 255))  # Green wipe

    def doTheater(self):
        print("Theater chase animations.")
        if self.color or self.wait_ms or self.iterations:
            self.theaterChase(self.color, self.wait_ms, self.iterations)
        else:
            self.theaterChase(Color(127, 127, 127))  # White theater chase
            self.theaterChase(Color(127, 0, 0))  # Red theater chase
            self.theaterChase(Color(0, 0, 127))  # Blue theater chase

    def doRainbow(self):
        print("Rainbow animations.")
        if self.color or self.wait_ms or self.iterations:
            self.rainbow(wait_ms, iterations)
            self.rainbowCycle(wait_ms, iterations)
            self.theaterChaseRainbow(wait_ms)
        else:   
            self.rainbow()
            self.rainbowCycle()
            self.theaterChaseRainbow()

    def doHass(self):
        print("HASS Entity State.")
        theState = self.checkState()
        # print('returned state ' + theState)

        if theState is False:
            self.colorWipe(Color(0, 0, 0), 10)
            exit()
        elif theState == "on":
            self.colorWipe(Color(0, 255, 0))  # Green wipe
        elif theState == "off":
            self.colorWipe(Color(255, 0, 0))  # Red wipe
        elif theState == "armed_home":
            self.colorWipe(Color(0, 0, 255))  # Red wipe
        elif theState == "pending":
            self.theaterChase(Color(127, 0, 0))  # Red theater chase
        elif theState == "exception":
            self.blink(Color(0, 127, 0))  # White theater chase

    # Define functions which animate LEDs in various ways.
    def colorWipe(self, color, wait_ms=50):
        """Wipe color across display a pixel at a time."""
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
            self.strip.show()
            time.sleep(wait_ms / 1000.0)

    def theaterChase(self, color, wait_ms=50, iterations=10):
        """Movie theater light style chaser animation."""
        for j in range(iterations):
            for q in range(3):
                for i in range(0, self.strip.numPixels(), 3):
                    self.strip.setPixelColor(i + q, color)
                self.strip.show()
                time.sleep(wait_ms / 1000.0)
                for i in range(0, self.strip.numPixels(), 3):
                    self.strip.setPixelColor(i + q, 0)

    def wheel(self, pos):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            theColor = Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            theColor = Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            theColor = Color(0, pos * 3, 255 - pos * 3)
        return theColor

    def rainbow(self, wait_ms=20, iterations=1):
        """Draw rainbow that fades across all pixels at once."""
        for j in range(256 * iterations):
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, self.wheel((i + j) & 255))
            self.strip.show()
            time.sleep(wait_ms / 1000.0)

    def rainbowCycle(self, wait_ms=20, iterations=5):
        """Draw rainbow that uniformly distributes itself across all pixels."""
        for j in range(256 * iterations):
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(
                    i, self.wheel((int(i * 256 / self.strip.numPixels()) + j) & 255)
                )
            self.strip.show()
            time.sleep(wait_ms / 1000.0)

    def theaterChaseRainbow(self, wait_ms=50):
        """Rainbow movie theater light style chaser animation."""
        for j in range(256):
            for q in range(3):
                for i in range(0, self.strip.numPixels(), 3):
                    self.strip.setPixelColor(i + q, self.wheel((i + j) % 255))
                self.strip.show()
                time.sleep(wait_ms / 1000.0)
                for i in range(0, self.strip.numPixels(), 3):
                    self.strip.setPixelColor(i + q, 0)

    def clearPixels(self):
        """ Clear the LEDs. """
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

    def blink(self, color, wait_ms=150, n=3):
        """Blink Color."""
        for x in range(n):
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, color)
            self.strip.show()
            time.sleep(wait_ms / 1000.0)
            self.clearPixels()
            time.sleep(wait_ms / 1000.0)

    def checkState(self):
        """ Connect to HASS and display state via LED. """
        url = "/api/states/" + self.entity
        response = hassConn(url=url, theType="GET")

        while True:
            try:
                theState = response.json()
                theState = theState["state"]
                print(entity + " is " + theState)
                # print(theState)
                # return theState
                if theState == "locked":
                    theState = "on"
                elif theState == "unlocked":
                    theState = "off"
                elif theState == "open":
                    theState = "on"
                elif theState == "closed":
                    theState = "off"
                elif theState == "armed":
                    theState = "on"
                elif theState == "armed_away":
                    theState = "on"
                elif theState == "disarmed":
                    theState = "off"
                elif theState == "home":
                    theState = "off"
                elif theState == "not_home":
                    theState = "on"
                break

            except KeyError:
                theText = json.loads(response.text)
                # print(theText)

                if theText["message"] == "Entity not found.":
                    print(entity + " " + theText["message"])
                    # return False
                    theState = False

        return theState


# Main program logic follows:
if __name__ == "__main__":
    # Process arguments
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "-c", "--clear", action="store_true", help="clear the display on exit", default=True
    )
    parser.add_argument("-a", "--all", action="store_true", help="All Examples")
    parser.add_argument("-w", "--wipe", action="store_true", help="Color Wipe")
    parser.add_argument("-t", "--theater", action="store_true", help="Theater Chase")
    parser.add_argument("-r", "--rainbow", action="store_true", help="Rainbow Cycle")
    parser.add_argument("-x", "--audio", choices=("hass","led", "both"), help="Audio Sync LED or HASS")
    parser.add_argument("-e", "--entity", action="store", help="Entity")
    parser.add_argument("-s", "--stop", action="store_true", help="Stop")
    args = parser.parse_args()

    try:
        print("----------------------------------------------")
        print("----------- Starting Color Server ------------")
        print("----------------------------------------------")
        while True:

            if args.wipe or args.all:
                neoPixelStrip(function="colorWipe")

            if args.theater or args.all:
                neoPixelStrip(function="theaterChase")

            if args.rainbow or args.all:
                neoPixelStrip(function="rainbow")

            if args.entity:
                neoPixelStrip(function="hassEntity", entity=args.entity)

            if args.audio:
                hass = True
                led = True
                if args.audio == "hass":
                    led = False
                elif args.audio == "led":
                    hass = False

                ProcessColor(hass=hass, led=led)

            if args.stop:
                print("Stop function")
                neoPixelStrip(function="clear")
                ProcessColor.exec_hass(0)
                print("----------------------------------------------")
                print("--------------- Shutting Down! ---------------")
                print("----------------------------------------------")
                exit(0)

            time.sleep(SLEEP)

    except KeyboardInterrupt:
        if args.clear:  # pylint: disable=too-many-function-args
            neoPixelStrip(function="clear")
            ProcessColor.exec_hass(0)
        print("----------------------------------------------")
        print("--------------- Shutting Down! ---------------")
        print("----------------------------------------------")
        exit(0)

