from socket import *
import platform
import select

_DEFAULT_MAX_QUEUE_SIZE = 20

if(platform.system() == 'Linux'):
    EVENT_READ = select.EPOLLIN
    EVENT_WRITE = select.EPOLLOUT
    EVENT_SHUTDOWN = select.EPOLLHUP
    EVENT_ERROR = select.EPOLLERR

class Socket(object):
    def __init__(self):
        self._socket = None
        self._onRead_callback = lambda: None
        self._onWrite_callback = lambda: None
        self._onError_callback = lambda: None
        self._onShutdown_callback = lambda: None
        self._max_queue_size = _DEFAULT_MAX_QUEUE_SIZE
        
    def getSocket(self):
        return self._socket

    def getFd(self):
        return self._socket.fileno()

    def close(self):
        self._socket.close()

    def shutdown(self):
        self._socket.shutdown(SHUT_RDWR)

    def setEvents(self, events):
        self._events = events

    def getEvents(self):
        return self._events

    def handleRead(self):
        self._onRead_callback()

    def handleWrite(self):
        self._onWrite_callback()

    def handleError(self):
        self._onError_callback()

    def handleShutdown(self):
        self._onShutdown_callback()

    def onRead(self, callback):
        self._onRead_callback = callback
    
    def onWrite(self, callback):
        self._onWrite_callback = callback

    def onError(self, callback):
        self._onError_callback = callback

    def onShutdown(self, callback):
        self._onShutdown_callback = callback

    def setMaxQueueSize(self, max_queue_size):
        self._max_queue_size = max_queue_size

    def keepAlive(self, value=True):
        self._socket.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1 if value else 0)

class TcpSocket(Socket):
    def __init__(self, addr=None):
        '''
        Initializes a TCP socket. Throws TinyNetError when failed.
        param:
            addr : a tuple with (ip, port)
        '''
        super(TcpSocket, self).__init__()
        if(addr is None):
            return
        
        self._socket = socket(AF_INET, SOCK_STREAM)
        self._socket.bind(addr)
    
    @staticmethod
    def createFrom(sock_obj):
        result = TcpSocket()
        result._socket = sock_obj
        return result

    def listen(self):
        self._socket.listen(self._max_queue_size)

    def connect(self, addr):
        self._socket.connect(addr)

    def accept(self):
        return self._socket.accept()

    def send(self, data):
        return self._socket.send(data)

    def recv(self, length):
        return self._socket.recv(length)

    def peek(self, length):
        return self._socket.recv(length, MSG_PEEK)

    def getAddr(self):
        return self._socket.getsockname()
        
    def getIp(self):
        return  self._socket.getsockname()[0]

    def getPort(self):
        return self._socket.getsockname()[1]

    def getRemoteAddr(self):
        return self._socket.getpeername()

    def getRemoteIp(self):
        return self.getRemoteAddr()[0]

    def getRemotePort(self):
        return self.getRemoteAddr()[1]

    def setKeepIdle(self, value):
        self._socket.setsockopt(SOL_TCP, TCP_KEEPIDLE, value)

    def setKeepInterval(self, value):
        self._socket.setsockopt(SOL_TCP, TCP_KEEPINTVL, value)

    def setKeepCount(self, value):
        self._socket.setsockopt(SOL_TCP, TCP_KEEPCNT, value)    

    


    
