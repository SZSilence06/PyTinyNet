from Socket import *
from Logger import *
from Util import *

_MAX_READ_SIZE = 256 * 1024

class TcpConnection(object):
    def __init__(self, tcpSocket):
        self._socket = tcpSocket
        self._user_data = {}
        self._remote_addr = tcpSocket.getRemoteAddr()

    def read(self, length = _MAX_READ_SIZE):
        return self._socket.recv(length)

    def peek(self, length = _MAX_READ_SIZE):
        return self._socket.peek(length)

    def send(self, data):
        self._socket.send(data)

    def getRemoteAddr(self):
        return self._remote_addr

    def getRemoteIp(self):
        return self._remote_addr[0]

    def getRemotePort(self):
        return self._remote_addr[1]

    def userData(self):
        return self._user_data

    def __getitem__(self, key):
        return self._user_data[key]

    def __setitem__(self, key, value):
        self._user_data[key] = value

    def __delitem__(self, key):
        del self._user_data[key]

class TcpServer(object):
    def __init__(self, event_dispatcher, addr):
        self._event_dispatcher = event_dispatcher
        self._socket = TcpSocket(addr)
        self._onRead_callback = lambda connection: None
        self._onConnClose_callback = lambda connection: None
        self._onError_callback = lambda connection: None
        self._connections = []

    def start(self):
        self._socket.listen()
        self._socket.onRead(lambda : self._handleAccept())
        self._socket.setEvents(EVENT_READ)
        self._event_dispatcher.getPoller().addSocket(self._socket)
        TN_INFO("TCP server started. Listening on " + self._socket.getIp() 
            + ":" + str(self._socket.getPort()))

    def _handleAccept(self):
        socketObj, addr = self._socket.accept()
        tcpSock = TcpSocket.createFrom(socketObj)
        tcpSock.setEvents(EVENT_READ | EVENT_ERROR | EVENT_SHUTDOWN)
        tcpSock.keepAlive()
        connection = TcpConnection(tcpSock)

        # set up callbacks
        tcpSock.onRead(lambda: self._handleRead(connection))
        tcpSock.onError(lambda: self._handleError(connection))

        self._event_dispatcher.getPoller().addSocket(tcpSock)
        self._connections.append(connection)
        TN_INFO("New connection established.")

    def _handleRead(self, connection):
        # test whether the connection has closed
        result = connection.peek(1024)
        if(result == ""):  # connection closed
            self._handleConnClose(connection)
        else:
            self._onRead_callback(connection)

    def _handleConnClose(self, connection):
        TN_INFO("connection to " + 
            Util.addrToStr(connection.getRemoteAddr()) +
            " closed.")
        self._onConnClose_callback(connection)
        self._connections.remove(connection)
        self._event_dispatcher.getPoller().removeSocket(connection._socket)

    def _handleError(self, connection):
        TN_INFO("connection to " + 
            Util.addrToStr(connection.getRemoteAddr()) +
            "encountered an error.")
        self._onError_callback()
        self._connections.remove(connection)
        self._event_dispatcher.getPoller().removeSocket(connection._socket)

    def onRead(self, callback):
        self._onRead_callback = callback

    def onConnClose(self, callback):
        self._onConnClose_callback = callback

    def onError(self, callback):
        self._onError_callback = callback


    
