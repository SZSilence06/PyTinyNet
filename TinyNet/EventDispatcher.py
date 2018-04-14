from Poller import *
from Logger import TN_INFO
import traceback

class EventDispatcher(object):
    def __init__(self):
        self._poller = Poller()
        self._servers = []
        
    def run(self):
        try:
            while True:
                self._poller.waitEvents()
        except TinyNetError, e:
            traceback.print_exc(e)
        except KeyboardInterrupt:
            self.__shutdown()
            raise

    def loopOnce(self):
        self._poller.peekEvents()

    def getPoller(self):
        return self._poller

    def addServer(self, server):
        self._servers.append(server)

    def __shutdown(self):
        for server in self._servers:
            server._onShutdown_callback()
        TN_INFO('Event dispatcher shutdown')

