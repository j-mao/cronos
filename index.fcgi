#!/usr/bin/env python

import os
import threading
import time

from flup.server.fcgi import WSGIServer

import cronos
from cronos.wsgi import application

os.environ["DJANGO_SETTINGS_MODULE"] = "cronos.settings"


def reloader():
    when = os.path.getmtime(cronos.__file__)
    while True:
        if when != os.path.getmtime(cronos.__file__):
            os._exit(3)
        time.sleep(1)


t = threading.Thread(target=reloader)
t.daemon = True
t.start()

WSGIServer(application).run()
