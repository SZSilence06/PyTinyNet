import sys
import os
import json
import socket
from struct import unpack
from Queue import Queue
from threading import Thread, Condition, Lock

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
sys.path.append('../common')

from Model import *
from Protocol import *
from RequestError import *

tinyNetDir = os.path.dirname(os.path.realpath(__file__)) + "/../../.."
sys.path.append("../../..")

from TinyNet.TcpClient import *

_DEFAULT_REQUEST_TIMEOUT = 60

class Request(object):
    def __init__(self):
        self._content = {}
        self._timeout = _DEFAULT_REQUEST_TIMEOUT

    def __setitem__(self, key, value):
        self._content[key] = value
        
    def __getitem__(self, key):
        return self._content[key]

    def setTimeout(self, timeout):
        self._timeout = timeout

    def getTimeout(self):
        return self._timeout

    def getContent(self):
        return self._content

class Response(object):
    def __init__(self):
        self._content = {}
        self._timeout = _DEFAULT_REQUEST_TIMEOUT

    def __setitem__(self, key, value):
        self._content[key] = value
        
    def __getitem__(self, key):
        return self._content[key]

    def getContent(self):
        return self._content

class Receiver(Thread):
    def __init__(self, client):
        super(Receiver, self).__init__()
        self._client = client
        self._need_quit = False
        self._response_queue = Queue()
        self._response_lock = Condition()

    def run(self):
        try:
            while self._need_quit == False:
                message = self._client.read()
                if len(message) == 0:
                    # the connection has shut down
                    self._client.close()
                    if self._need_quit == False:
                        # server closed connection
                        self._client._onServerCloseConnection_callback()
                    break
                if Protocol.isResponse(message):
                    self._response_lock.acquire()
                    self._response_queue.put(message)
                    self._response_lock.notify()
                    self._response_lock.release()
                else:
                    Thread(self._client._handlePush(message)).start()
        except socket.error, e:
            self._client._onDisconnected_callback()

    def getOneResponse(self, timeout):
        self._response_lock.acquire()
        # try to get one response from the response queue
        try:
            if self._response_queue.empty():
                self._response_lock.wait(timeout)
                if(self._response_queue.empty()):
                    # request time out
                    raise RequestTimeoutError()  
            response_message = self._response_queue.get()    
            return response_message
        finally:
            self._response_lock.release()

    def stop(self):
        self._need_quit = True

class MainClient(TcpClient):
    def __init__(self):
        super(MainClient, self).__init__()
        self._receiver = None
        self._closed = True
        self._lock = Lock()

        self._action_handler = {}

        self._onServerCloseConnection_callback = lambda: None
        self._onDisconnected_callback = lambda: None

    def read(self):
        inbuf = super(MainClient, self).recv(4)
        if len(inbuf) == 0:
            return inbuf
        bytes_to_read = unpack("!l", inbuf)[0]
        income_packages = []
        while bytes_to_read > 0:
            inbuf = super(MainClient, self).recv(bytes_to_read)
            if len(inbuf) == 0:
                return inbuf
            income_packages.append(inbuf)
            bytes_to_read -= len(inbuf)
        complete_package = b''.join(income_packages)
        message = unpack("!" + str(len(complete_package)) + "s", 
            complete_package)[0]
        return message

    def send(self, message):
        super(MainClient, self).send(Protocol.makeMessage(message))

    def connect(self, addr):
        super(MainClient, self).connect(addr)
        self._receiver = Receiver(self)
        self._receiver.start()
        self._closed = False

    def shutdown(self):
        self._lock.acquire()
        if self._closed == False:
            if self._receiver:
                self._receiver.stop()
            super(MainClient, self).shutdown()
        self._lock.release()

    def close(self):
        self._lock.acquire()
        self._closed = True
        self._lock.release()
        super(MainClient, self).close()

    def _sendRequest(self, request):
        super(MainClient, self).send(Protocol.makeMessageFromDict(request.getContent()))

    def getResponse(self, request):
        # potential bug here. What if a second request acquire the lock before the first request?
        self._sendRequest(request) 
        response_message = self._receiver.getOneResponse(request.getTimeout())   
        response = Response()
        response._content = json.loads(response_message)
        return response

    def _handlePush(self, incoming_package):
        json_obj = loads(incoming_package)
        action = json_obj['action']
        if action in self._action_handler:
            self._action_handler[action](json_obj)  

    def registerActionHandler(self, action, handler):
        self._action_handler[action] = handler
    
    def unregisterActionHandler(self, action):
        if action in self._action_handler:
            del self._action_handler[action]
    
    def onServerCloseConnection(self, callback):
        self._onServerCloseConnection_callback = callback

    def onDisconnected(self, callback):
        self._onDisconnected_callback = callback
        

       


    

        

        

    
