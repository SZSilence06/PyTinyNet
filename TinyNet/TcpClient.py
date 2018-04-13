from Socket import *
from Logger import *
from Util import *
from Connection import TcpConnection

_DEFAULT_MAX_READ_SIZE = 1024 * 256

class TcpClient(object):
    def __init__(self):
        self._socket = TcpSocket(('0.0.0.0', 0))
        self._connection = None

    def __del__(self):
        self._socket.close()

    def connect(self, addr):
        TN_INFO("connecting to " + Util.addrToStr(addr))
        self._socket.connect(addr)
        TN_INFO("connected to " + Util.addrToStr(addr))
        self._connection = TcpConnection(self._socket)

    def send(self, message):
        self._connection.send(message)

    def recv(self):
        while self._connection.tryReadNextPackage() == False:  # loop until we get the complete package
            pass
        return self._connection.read()

    def close(self):
        self._socket.close()

    def shutdown(self):
        self._socket.shutdown()
        self._connection = None

    

    


