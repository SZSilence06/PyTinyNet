import sys
import os

currentDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(currentDir + '/..')

from TinyNet.TcpClient import TcpClient
from TinyNet.Logger import Logger, LogLevel

if __name__ == '__main__':
    Logger.getInstance().setLogLevel(LogLevel.DEBUG)
    client = TcpClient()
    client.connect(("127.0.0.1", 3000))
    data = raw_input("enter data to send:")
    client.send(data)
    client.send(',cnm')
    data = client.recv()
    print "received data:" + data
    