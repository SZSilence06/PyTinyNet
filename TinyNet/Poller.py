import select
import platform
from Error import *
from Socket import *
from Logger import *

_DEFAULT_MAX_TIMEOUT = 20
_DEFAULT_MAX_EVENTS = 1000

class PollerImpl(object):
    def __init__(self):
        self._timeout = _DEFAULT_MAX_TIMEOUT
        self._max_events = _DEFAULT_MAX_TIMEOUT

    def setMaxTimeout(self, maxTimeout):
        self._timeout = maxTimeout

    def getMaxTimeout(self):
        return self._timeout

    def setMaxEvents(self, maxEvents):
        self._max_events = maxEvents

    def getMaxEvents(self):
        return self._max_events

class PollerKqueue(PollerImpl):
    pass # to be continued

class PollerIocp(PollerImpl):
    pass  # to be continued 

class PollerEpoll(PollerImpl):
    def __init__(self):
        super(PollerEpoll, self).__init__()
        self._epoll = select.epoll()
        self._living_sockets = {}

    def addSocket(self, socket):
        try:
            self._epoll.register(socket.getSocket(), socket.getEvents())
            self._living_sockets[socket.getFd()] = socket
        except error, e:
            raise TinyNetError("Failed to add socket to poller! ") + str(e)
        
    def removeSocket(self, socket):
        self._epoll.unregister(socket.getFd())
        del self._living_sockets[socket.getFd()]
        socket.close()
    
    def waitEvents(self):
        events = self._epoll.poll(self.getMaxTimeout(), self.getMaxEvents())
        for fd, event in events:
            socket = self._living_sockets[fd]
            if(event & EVENT_ERROR):
                socket.handleError()
            if(event & EVENT_SHUTDOWN):
                socket.handleShutdown()
            if(event & EVENT_READ):
                socket.handleRead()
            if(event & EVENT_WRITE):
                socket.handleWrite()                      

class Poller(object):
    def __init__(self):
        sysType = platform.system() 
        if(sysType == 'Linux'):
            self._poller = PollerEpoll()
        elif(sysType == 'Windows'):
            self._poller = PollerIocp()
        elif(sysType == 'Darwin'):  # Mac OS X
            self._poller = PollerKqueue()
        else:
            raise TinyNetError('Platform OS not supported.')

    def setMaxTimeout(self, maxTimeout):
        self._poller.setMaxTimeout(maxTimeout)

    def getMaxTimeout(self):
        return self._poller.getMaxTimeout()

    def setMaxEvents(self, maxEvents):
        self._poller.setMaxEvents(maxEvents)

    def getMaxEvents(self):
        return self._poller.getMaxEvents()

    def addSocket(self, socket):
        self._poller.addSocket(socket)

    def removeSocket(self, socket):
        self._poller.removeSocket(socket)

    def waitEvents(self):
        self._poller.waitEvents()



