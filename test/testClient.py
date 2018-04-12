import sys

sys.path.append('..')

from TinyNet.TcpClient import *

if __name__ == '__main__':
    client = TcpClient()
    client.connect(("127.0.0.1", 3000));
    data = raw_input("enter data to send:")
    client.send(str(data))
    client.send(',cnm')
    data = client.recv()
    print "received data:" + data
    