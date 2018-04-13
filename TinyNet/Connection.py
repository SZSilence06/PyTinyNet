from Error import ConnectionClosedError
import Config
import struct
from Logger import TN_DEBUG

class TcpConnection(object):
    def __init__(self, tcpSocket):
        self._socket = tcpSocket
        self._user_data = {}
        self._remote_addr = tcpSocket.getRemoteAddr()
        self._sendbuf = []
        self._recvbuf = []
        self._nextPackageSize = 0

    def read(self, encode=None):
        '''get message from receive buffer'''
        result = ''.join(self._recvbuf)
        self._recvbuf = []
        if encode:
            result = result.decode(encode)
        TN_DEBUG('received complete pacakge : ' + repr(self._sendbuf))
        return result

    def send(self, data, encode=None):
        if encode:
            data = data.encode(encode)
        self._sendbuf = struct.pack('!' + Config.PACKAGE_SIZE_FORMAT, len(data))
        self._sendbuf += data
        TN_DEBUG('send length %d complete pacakge : ' % len(data) + repr(self._sendbuf))
        self._socket.send(self._sendbuf)

    def getSocket(self):
        return self._socket

    def getRemoteAddr(self):
        return self._remote_addr

    def getRemoteIp(self):
        return self._remote_addr[0]

    def getRemotePort(self):
        return self._remote_addr[1]

    def getError(self):
        return self._socket.getPendingError()

    def userData(self):
        return self._user_data

    def __getitem__(self, key):
        return self._user_data[key]

    def __setitem__(self, key, value):
        self._user_data[key] = value

    def __delitem__(self, key):
        del self._user_data[key]

    def tryReadNextPackage(self):
        ''' read socket to get a complete package.
        return true if complete package has been read.
        '''

        if len(self._recvbuf) == 0:
            # get a new package, try to read package length
            ssize = Config.PACKAGE_SIZE_SIZE
            data = self._socket.peek(ssize)
            if data == "":
                raise ConnectionClosedError()
            if(len(data) < ssize):
                return False

            self._nextPackageSize = struct.unpack('!' + Config.PACKAGE_SIZE_FORMAT, data[:ssize])[0]
            TN_DEBUG('received next package size ' + str(self._nextPackageSize))
            self._socket.recv(ssize)

        # read remaining part of the next package
        data = self._socket.recv(self._nextPackageSize - len(self._recvbuf))
        TN_DEBUG('received data : ' + str(data))
        self._recvbuf += data
        return len(self._recvbuf) == self._nextPackageSize

    
