# -*- coding: utf-8 -*-

import os
# import sys
# import termios
# import tty
# import pigpio
# import time
# from threading import Thread
import cherrypy
import subprocess
import signal


class ColorServer(object):

    def __init__(self):
        self._theprocess = None
        self._processArgs = None

    def _popen(self):
        if self._theprocess:
            print('PID: %s' % self._theprocess.pid)
            subprocess.check_call(["sudo", "kill", str(self._theprocess.pid)])
            self._theprocess = None
            print("Killed the Process.")
        if self._processArgs:
            print("Starting a new Process.")
            self._theprocess = subprocess.Popen(self._processArgs)
            print('PID: %s' % self._theprocess.pid)

    @cherrypy.expose
    def index(self):
        return """<html>
        <head>
        <title>Color Controller</title>
        <link href="/static/css/style.css" rel="stylesheet">
        <meta id="viewport" name="viewport" content= "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0" />
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
        </head>
        <body class="outside">
            <div class="controller">
            <form style='display: inline-block; padding: 5px;' method="get" action="turnOn">
                <button type="submit" class="btn btn-default btn-lg" id="clickON">Turn the lights on!</button>
            </form>
            <form style='display: inline-block; padding: 5px;' method="get" action="turnOff">
                <button type="submit" class="btn btn-default btn-lg" id="clickOFF">Turn the lights off...</button>
            </form>
            <br>
            <p>
                <h3>Choose a Mode</h3>
                <form style='display: inline-block; padding: 5px;' method="get" action="chill">
                <button type="submit" class="btn btn-default" id="mode1">Chill Mode</button>
                </form>
                <form style='display: inline-block; padding: 5px;' method="get" action="energy">
                <button type="submit" class="btn btn-default" id="mode2">Energy Mode</button>
                </form>
                <form style='display: inline-block; padding: 5px;' method="get" action="party">
                <button type="submit" class="btn btn-default" id="mode3">Party Mode</button>
                </form>
            </p>
            <p>
                <h3>Go to Music?</h3>
                <form style='display: inline-block; padding: 5px;' method="get" action="listenOn">
                <button type="submit" class="btn btn-default" id="listenON">Yes</button>
                </form>
                <form style='display: inline-block; padding: 5px;' method="get" action="listenOff">
                <button type="submit" class="btn btn-default" id="listenOFF">No</button>
                </form>
            </p>
            </div>
        </body>
        </html>"""

    @cherrypy.expose
    def turnOn(self):
        print("Turn On")
        self._processArgs = ["sudo", "python3", "color_script_web.py", "-a"]
        self._popen()
        raise cherrypy.HTTPRedirect("/index")

    @cherrypy.expose
    def turnOff(self):
        print("Turn Off")
        self._processArgs = ["sudo", "python3", "color_script_web.py", "-s"]
        self._popen()
        #os.system("python3 make_file.py c")
        raise cherrypy.HTTPRedirect("/index")

    @cherrypy.expose
    def chill(self):
        print("Chill = theater chase")
        self._processArgs = ["sudo", "python3", "color_script_web.py", "-t"]
        self._popen()
        #os.system("python3 make_file.py 1")
        raise cherrypy.HTTPRedirect("/index")

    @cherrypy.expose
    def energy(self):
        print("Energy = Color Wipe")
        self._processArgs = ["sudo", "python3", "color_script_web.py", "-w"]
        self._popen()
        #os.system("python3 make_file.py 2")
        raise cherrypy.HTTPRedirect("/index")

    @cherrypy.expose
    def party(self):
        print("Party = Rainbow")
        self._processArgs = ["sudo", "python3", "color_script_web.py", "-r"]
        self._popen()
        #os.system("python3 make_file.py 3")
        raise cherrypy.HTTPRedirect("/index")

    @cherrypy.expose
    def listenOn(self):
        self._processArgs = ["sudo", "python3", "color_script_web.py"]
        self._popen()
        #os.system("python3 make_file.py y")
        raise cherrypy.HTTPRedirect("/index")

    @cherrypy.expose
    def listenOff(self):
        self._processArgs = ["sudo", "python3", "color_script_web.py"]
        self._popen()
        #os.system("python3 make_file.py n")
        raise cherrypy.HTTPRedirect("/index")


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public'
        }
    }
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.quickstart(ColorServer(), '/', conf)
