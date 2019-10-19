# -*- coding: utf-8 -*-

import os
import cherrypy
import subprocess
import signal
import re
import logging

logging.basicConfig(level=logging.DEBUG)
_LOG = logging.getLogger(__name__)


class ColorServer():
    def __init__(self):
        self._theprocess = None
        self._processArgs = None

    def _popen(self):
        if self._theprocess:
            _LOG.debug("PID: %s" % self._theprocess.pid)
            self._theprocess.send_signal(signal.SIGINT)
            self._theprocess.wait()
            self._theprocess = None
            _LOG.debug("Killed the Process.")

        if self._processArgs:
            _LOG.debug("Starting a new Process.")
            self._theprocess = subprocess.Popen(self._processArgs)
            _LOG.debug("PID: %s" % self._theprocess.pid)

    @cherrypy.expose
    def index(self, error=None):
        html = """<html>
        <head>
            <title>Color Controller</title>
            <link href="/static/css/style.css" rel="stylesheet">
            <meta id="viewport" name="viewport" content= "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0" />
            <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
        </head>
        <body class="outside">
            <div class="controller">
                <div><h3>LED Demos</h3>
                    <form style='display: inline-block; padding: 5px;' method="get" action="all">
                    <button type="submit" class="btn btn-default" id="all">All</button>
                    </form>
                    <form style='display: inline-block; padding: 5px;' method="get" action="wipe">
                    <button type="submit" class="btn btn-default" id="wipe">Wipe</button>
                    </form>
                    <form style='display: inline-block; padding: 5px;' method="get" action="theater">
                    <button type="submit" class="btn btn-default" id="theater">Theater</button>
                    </form>
                    <form style='display: inline-block; padding: 5px;' method="get" action="rainbow">
                    <button type="submit" class="btn btn-default" id="rainbow">Rainbow</button>
                    </form></div>
                <div><h3>Audio Sync</h3>
                    <form style='display: inline-block; padding: 5px;' method="get" action="audioSync">
                    <input type="radio" name="toSync" value="hass"> Hass
                    <input type="radio" name="toSync" value="led"> Led
                    <input type="radio" name="toSync" value="both"> Both
                    <button type="submit" class="btn btn-default" id="audioSync">Audio Sync</button>
                    </form></div>
                <div><h3>Home Assistant</h3>"""
        if error == "entity":
            html += """<BR><font color=red>Invalid Entity!</font><BR>"""

        html += """
                    <form style='display: inline-block; padding: 5px;' method="get" action="hassEntity">
                    <input type="text" name="entity" placeholder="light.living_room">
                    <button type="submit" class="btn btn-default" id="hassEntity">Hass Entity</button>
                    </form></div>
                <div><h3>STOP</h3>
                    <form style='display: inline-block; padding: 5px;' method="get" action="turnOff">
                    <button type="submit" class="btn btn-default" id="turnOff">Stop Function</button>
                    </form></div>
            </div>
        </body>
        </html>"""

        return html

    @cherrypy.expose
    def all(self):
        _LOG.info("All Demos")
        self._processArgs = ["python3", "color_script.py", "-a"]
        self._popen()
        raise cherrypy.HTTPRedirect("/index")

    @cherrypy.expose
    def wipe(self):
        _LOG.info("Wipe Demo")
        self._processArgs = ["python3", "color_script.py", "-w"]
        self._popen()
        raise cherrypy.HTTPRedirect("/index")

    @cherrypy.expose
    def theater(self):
        _LOG.info("Theater Chase Demo")
        self._processArgs = ["python3", "color_script.py", "-t"]
        self._popen()
        raise cherrypy.HTTPRedirect("/index")

    @cherrypy.expose
    def rainbow(self):
        _LOG.info("Rainbow Demo")
        self._processArgs = ["python3", "color_script.py", "-r"]
        self._popen()
        raise cherrypy.HTTPRedirect("/index")

    @cherrypy.expose
    def audioSync(self, toSync):
        _LOG.info("Audio Sync")
        self._processArgs = ["python3", "color_script.py", "-x=" + toSync]
        self._popen()
        raise cherrypy.HTTPRedirect("/index")

    @cherrypy.expose
    def hassEntity(self, entity):
        _LOG.info("Hass Entity")
        rex = re.compile("^[a-z_]+.[a-z_0-9]+$")
        if rex.match(entity):
            _LOG.debug("True")
            self._processArgs = ["python3", "color_script.py", "-e " + entity]
            self._popen()
            raise cherrypy.HTTPRedirect("/index")
        else:
            raise cherrypy.HTTPRedirect("/index?error=entity")

    @cherrypy.expose
    def turnOff(self):
        _LOG.info("Turn Off")
        self._processArgs = ["python3", "color_script.py", "-s"]
        self._popen()
        raise cherrypy.HTTPRedirect("/index")


if __name__ == "__main__":
    conf = {
        "/": {"tools.sessions.on": True, "tools.staticdir.root": os.path.abspath(os.getcwd())},
        "/static": {"tools.staticdir.on": True, "tools.staticdir.dir": "./public"},
    }
    if os.geteuid() == 0:
        cherrypy.process.plugins.DropPrivileges(cherrypy.engine, uid=0, gid=0).subscribe()
    cherrypy.config.update({"server.socket_host": "0.0.0.0"})
    cherrypy.quickstart(ColorServer(), "/", conf)
