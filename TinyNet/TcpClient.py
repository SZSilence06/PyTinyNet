from socket import *
from Socket import *
from Logger import *
from Util import *

_DEFAULT_MAX_READ_SIZE = 1024 * 256

class TcpClient(object):
    def __init__(self):
        self._socket = TcpSocket(('0.0.0.0', 0))

    def __del__(self):
        self._socket.close()

    def connect(self, addr):
        TN_INFO("connecting to " + Util.addrToStr(addr))
        self._socket.connect(addr)
        TN_INFO("connected to " + Util.addrToStr(addr))

    def send(self, message):
        self._socket.send(message)

    def recv(self, length = _DEFAULT_MAX_READ_SIZE):
        return self._socket.recv(length)

    def close(self):
        self._socket.close()

    def shutdown(self):
        self._socket.shutdown()

    

    


