from Poller import *
import traceback

class EventDispatcher(object):
    def __init__(self):
        self._poller = Poller()
        
    def run(self):
        try:
            while True:
                self._poller.waitEvents()
        except TinyNetError, e:
            traceback.print_exc(e)

    def getPoller(self):
        return self._poller
