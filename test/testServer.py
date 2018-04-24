import sys
import os

currentDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(currentDir + '/..')

from TinyNet.EventDispatcher import *
from TinyNet.TcpServer import *
from TinyNet.Logger import Logger, LogLevel

def serverOnRead(connection):
    print "Received data : " + connection.read()
    connection.send("hello") 

if __name__ == '__main__':
    Logger.getInstance().setLogLevel(LogLevel.DEBUG)
    dispatcher = EventDispatcher()
    dispatcher.getPoller().setMaxTimeout(50)
    server = TcpServer(dispatcher, ("127.0.0.1", 3000))
    server.onRead(serverOnRead)
    server.start()
    dispatcher.run()

