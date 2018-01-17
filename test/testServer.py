import sys

sys.path.append('..')

from TinyNet.EventDispatcher import *
from TinyNet.TcpServer import *

def serverOnRead(connection):
    print "Received data : " + connection.read()
    connection.send("fuck you") 

if __name__ == '__main__':
    dispatcher = EventDispatcher()
    dispatcher.getPoller().setMaxTimeout(50)
    server = TcpServer(dispatcher, ("192.168.153.128", 3000))
    server.onRead(serverOnRead)
    server.start()
    dispatcher.run()

