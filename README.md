# audio-led-sync
Sync LED lights and home assistant lights to audio

It is a work in progress.

Made for raspberry pi. ws2812 led or home assistant instance on another server.
Options -c, -a, w, t, r, e, x for ws2812 leds
Options -e, -x for home assistant
-e to check home assistant for an entity and display a color on the leds

-x hass,led, or both to sync audio via usb mic connected to rpi and display colors based on pitch/volume.

There is a cherrypy server script that is not yet implimented.

cli options:
```
usage: color_script.py [-h] [-c] [-a] [-w] [-t] [-r] [-x {hass,led,both}]
                       [-e ENTITY] [-s]

optional arguments:
  -h, --help            show this help message and exit
  -c, --clear           clear the display on exit
  -a, --all             All Examples
  -w, --wipe            Color Wipe
  -t, --theater         Theater Chase
  -r, --rainbow         Rainbow Cycle
  -x {hass,led,both}, --audio {hass,led,both}
                        Audio Sync LED or HASS
  -e ENTITY, --entity ENTITY
                        Entity
  -s, --stop            Stop
```