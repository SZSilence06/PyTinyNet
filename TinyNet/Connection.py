import socket
import errno
from Error import ConnectionClosedError
import Config
import struct
import copy
from Logger import TN_DEBUG
from Util import Util

class TcpConnection(object):
    def __init__(self, tcpSocket):
        self._socket = tcpSocket
        self._user_data = {}
        self._remote_addr = tcpSocket.getRemoteAddr()
        self._sendbuf = ''
        self._recvbuf = ''
        self._nextPackageSize = 0
        self._received_complete_package = False

    def read(self, encode=None):
        '''get message from receive buffer'''
        TN_DEBUG('received complete pacakge : ' + repr(self._recvbuf))
        result = copy.copy(self._recvbuf)
        self._recvbuf = ''
        self._received_complete_package = False
        if encode:
            result = result.decode(encode)
        return result

    def send(self, data, encode=None):
        if encode:
            data = data.encode(encode)
        self._sendbuf = struct.pack('!' + Config.PACKAGE_SIZE_FORMAT, len(data))
        self._sendbuf += data
        TN_DEBUG('send length %d complete pacakge : ' % len(data) + repr(data))
        self._socket.send(self._sendbuf)

    def close(self):
        self._socket.close()

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
        if self._received_complete_package:
            # there already exists a complete package to be read
            return True

        try:
            if self._nextPackageSize == 0:
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
            TN_DEBUG('received data : ' + repr(data))
            self._recvbuf += data
            if len(self._recvbuf) == self._nextPackageSize:
                self._received_complete_package = True
                self._nextPackageSize = 0
            return self._received_complete_package

        except socket.error, e:
            if e.errno == errno.ECONNRESET:
                # regard connection reset as normally connection close
                TN_DEBUG('connection to ' + Util.addrToStr(self.getRemoteAddr()) + ' reset.')
                raise ConnectionClosedError()
            elif e.errno == errno.EWOULDBLOCK:
                # no data to read for nonblock socket
                return False
            raise 

    
