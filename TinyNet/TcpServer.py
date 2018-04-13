import socket
import errno
from Socket import TcpSocket, EVENT_READ, EVENT_WRITE, EVENT_ERROR
from Logger import *
from Util import *
from Error import ConnectionClosedError
from Connection import TcpConnection

_MAX_READ_SIZE = 256 * 1024
_DEFAULT_KEEP_IDLE = 60
_DEFAULT_KEEP_INTERVAL = 10
_DRFAULT_KEEP_COUNT = 5

class TcpServer(object):
    def __init__(self, event_dispatcher, addr):
        self._event_dispatcher = event_dispatcher
        self._socket = TcpSocket(addr)
        self._onRead_callback = lambda connection: None
        self._onConnClose_callback = lambda connection: None
        self._onError_callback = lambda connection: None
        self._connections = []

        self._keep_idle = _DEFAULT_KEEP_IDLE
        self._keep_interval = _DEFAULT_KEEP_INTERVAL
        self._keep_count = _DRFAULT_KEEP_COUNT

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
        tcpSock.setEvents(EVENT_READ | EVENT_ERROR)
        tcpSock.keepAlive()
        tcpSock.setKeepIdle(self._keep_idle)
        tcpSock.setKeepInterval(self._keep_interval)
        tcpSock.setKeepCount(self._keep_count)
        connection = TcpConnection(tcpSock)

        # set up callbacks
        tcpSock.onRead(lambda: self._handleRead(connection))
        tcpSock.onError(lambda: self._handleError(connection, None))

        self._event_dispatcher.getPoller().addSocket(tcpSock)
        self._connections.append(connection)
        TN_INFO("New connection established.")

    def _handleRead(self, connection):
        try:
            if connection.tryReadNextPackage():
                self._onRead_callback(connection)
        except ConnectionClosedError:
            self._handleConnClose(connection)
        except socket.error, e:
            if e.errno == errno.ECONNRESET:
                # regard connection reset as normally connection close
                self._handleConnClose(connection) 
            else:
                self._handleError(connection, e)

    def _handleConnClose(self, connection):
        TN_INFO("connection to " + 
            Util.addrToStr(connection.getRemoteAddr()) +
            " closed.")
        self._onConnClose_callback(connection)
        self._connections.remove(connection)
        self._event_dispatcher.getPoller().removeSocket(connection._socket)

    def _handleError(self, connection, error):
        if error is None:
            error = connection.getError()
        TN_INFO("connection to " + 
            Util.addrToStr(connection.getRemoteAddr()) +
            " encountered an error: " + str(error))
        self._onError_callback(connection)
        self._connections.remove(connection)
        self._event_dispatcher.getPoller().removeSocket(connection._socket)

    def onRead(self, callback):
        self._onRead_callback = callback

    def onConnClose(self, callback):
        self._onConnClose_callback = callback

    def onError(self, callback):
        self._onError_callback = callback

    def setKeepIdle(self, value):
        self._keep_idle = value

    def setKeepInterval(self, value):
        self._keep_interval = value

    def setKeepCount(self, value):
        self._keep_count = value

    
