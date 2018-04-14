import select
import platform
from Error import *
from Socket import *
from Logger import *

_DEFAULT_MAX_TIMEOUT = 20
_DEFAULT_MAX_EVENTS = 1000

_sysType = platform.system() 

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

if _sysType == 'Darwin':
    class PollerKqueue(PollerImpl):
        pass # to be continued

elif _sysType == 'Windows':
    class PollerIocp(PollerImpl):
        def __init__(self):
            pass

        def addSocket(self, socket):
            pass

        def removeSocket(self, socket):
            pass

        def waitEvents(self):
            pass

elif _sysType == 'Linux':    
    class PollerEpoll(PollerImpl):
        def __init__(self):
            super(PollerEpoll, self).__init__()
            self._epoll = select.epoll()
            self._living_sockets = {}

        def addSocket(self, socket):
            self._epoll.register(socket.getSocket(), socket.getEvents())
            self._living_sockets[socket.getFd()] = socket
            
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
                    continue
                if(event & EVENT_READ):
                    socket.handleRead()
                if(event & EVENT_WRITE):
                    socket.handleWrite()

        def peekEvents(self):
            raise NotImplementedError

class PollerSelect(PollerImpl):
    def __init__(self):
        self._living_sockets = {}
        self._rlist = [] # fd wait for reading
        self._wlist = [] # fd wait for writing
        self._xlist = [] # fd wait for exceptions

    def addSocket(self, socket):
        fd = socket.getFd()
        self._living_sockets[fd] = socket

        # register event listeners
        events = socket.getEvents()
        if(events & EVENT_READ):
            self._rlist.append(fd)
        if(events & EVENT_WRITE):
            self._wlist.append(fd)
        if(events & EVENT_ERROR):
            self._xlist.append(fd)

    def removeSocket(self, socket):
        fd = socket.getFd()
        del self._living_sockets[fd]

        # remove event listeners
        events = socket.getEvents()
        if(events & EVENT_READ):
            self._rlist.remove(fd)
        if(events & EVENT_WRITE):
            self._wlist.remove(fd)
        if(events & EVENT_ERROR):
            self._xlist.remove(fd)

    def waitEvents(self):
        result = select.select(self._rlist, self._wlist, self._xlist, self._timeout)
        rlist = result[0]
        wlist = result[1]
        xlist = result[2]
        for fd in rlist:
            self._living_sockets[fd].handleRead()
        for fd in wlist:
            self._living_sockets[fd].handleWrite()
        for fd in xlist:
            self._living_sockets[fd].handleError()

    def peekEvents(self):
        result = select.select(self._rlist, self._wlist, self._xlist, 0)
        rlist = result[0]
        wlist = result[1]
        xlist = result[2]
        for fd in rlist:
            self._living_sockets[fd].handleRead()
        for fd in wlist:
            self._living_sockets[fd].handleWrite()
        for fd in xlist:
            self._living_sockets[fd].handleError()                      

class Poller(object):
    def __init__(self):
        global _sysType
        if(_sysType == 'Linux'):
            self._poller = PollerEpoll()
        elif(_sysType == 'Windows'):
            # self._poller = PollerIocp()
            self._poller = PollerSelect()
        elif(_sysType == 'Darwin'):  # Mac OS X
            # self._poller = PollerKqueue()
            self._poller = PollerSelect()
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

    def peekEvents(self):
        self._poller.peekEvents()



