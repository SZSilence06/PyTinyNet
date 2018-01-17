#!usr/env/bin python

import os
import sys
import json
import traceback
from struct import unpack, unpack_from
from datetime import datetime, timedelta

currentDir = os.path.dirname(os.path.realpath(__file__))
tinyNetDir = currentDir + "/../../.."
sys.path.append("../../..")

sys.path.append('.')
sys.path.append('../common')

from TinyNet.EventDispatcher import *
from TinyNet.TcpServer import *
from TinyNet.Logger import *
from DAO import UserDAO
from Protocol import *
from RequestError import *

def tryGetKey(d, key):
    if key not in d:
        raise InvalidRequestError("key '" + str(key) + "' not found.")
    return d[key]

class User(object):
    def __init__(self, username, connection):
        self._username = username
        self._connection = connection
        self._room = None
        self._login_time = None

    def getName(self):
        return self._username

    def getConnection(self):
        return self._connection

    def setRoom(self, room):
        self._room = room
    
    def getRoom(self):
        return self._room

    def setLoginTime(self, login_time):
        self._login_time = login_time

    def getLoginTime(self):
        return self._login_time

class Room(object):
    def __init__(self, name, creator):
        self._name = name
        self._master = creator
        self._users = []

    def getName(self):
        return self._name

    def getUsers(self):
        return self._users

    def addUser(self, user):
        self._users.append(user)

    def removeUser(self, user):
        self._users.remove(user)

    def getMaster(self):
        return self._master

    def toDict(self):
        d = {}
        d['name'] = self._name
        d['users'] = [user.getName() for user in self._users]
        return d

class MainServer(TcpServer):
    def __init__(self, event_dispatcher, addr):
        super(MainServer, self).__init__(event_dispatcher, addr)
        self._online_users = []
        self._rooms = {}

        self.onRead(self.mainServerOnRead)
        self.onConnClose(self.mainServerOnConnClose)
        self.onError(self.mainServerOnConnClose)

    def mainServerOnRead(self, connection):
        connection_data = connection.userData()
        if('bytes_to_read' not in connection_data):
            connection_data['bytes_to_read'] = 0
        read_length = connection_data['bytes_to_read']
        if(read_length == 0):
            # read the first 4 bytes of the incoming message to get message length
            read_length = unpack('!l', connection.read(4))[0]
            connection_data['bytes_to_read'] = read_length
        request = connection.read(read_length)
        connection_data['bytes_to_read'] -= read_length

        try:
            self.parseRequest(connection, request)
        except InvalidRequestError, e:
            response = {}
            response['code'] = Code.INVALID_REQUEST
            response['message'] = 'Invalid request : ' + str(e)
            connection.send(Protocol.makeMessageFromDict(response))
        except RequestFailedError, e:
            response = {}
            response['code'] = Code.REQUEST_FAILED
            response['message'] = str(e)
            connection.send(Protocol.makeMessageFromDict(response))
        except Exception, e:
            TN_ERROR(str(e))
            traceback.print_exc(e)
            response = {}
            response['code'] = Code.INTERNAL_ERROR
            response['message'] = 'Server internal error : ' + str(e)
            connection.send(Protocol.makeMessageFromDict(response))

    def mainServerOnConnClose(self, connection):
        if 'user' in connection.userData():
            # user log out
            self.logout(connection['user'])

    def parseRequest(self, connection, request):
        jsonString = request
        decoded_request = json.loads(jsonString)
        if('action' not in decoded_request):
            raise InvalidRequestError("key 'action' not found.")
        action = decoded_request['action']
        self.onAction(action, connection, decoded_request)

    def onAction(self, action, connection, decoded_request):
        if(action == 'register'):
            self.onRegister(connection, decoded_request)
        elif(action == 'login'):
            self.onLogin(connection, decoded_request)
        elif(action == 'broadcast'):
            self.onBroadcast(connection, decoded_request)
        elif(action == 'create_room'):
            self.onCreateRoom(connection, decoded_request)
        elif(action == 'get_rooms'):
            self.onGetRooms(connection)
        elif(action == 'exit_room'):
            self.onExitRoom(connection)
        elif(action == 'enter_room'):
            self.onEnterRoom(connection, decoded_request)
        elif(action == 'send_room_message'):
            self.onSendRoomMessage(connection, decoded_request)
        else:
            raise InvalidRequestError("not supported 'action' value:" + action)

    def onRegister(self, connection, decoded_request):
        if('username' not in decoded_request):
            raise InvalidRequestError("key 'username' not found.")
        username = decoded_request['username']
        
        if('password' not in decoded_request):
            raise InvalidRequestError("key 'password' not found.")
        password = decoded_request['password']

        dao = UserDAO.getInstance()
        if(dao.existUser(username)):
            raise RequestFailedError('Username already exists.')
        
        dao.addUser(username, password)
        response = {'code' : Code.SUCCESS}
        response['message'] = 'User successfully added.'
        connection.send(Protocol.makeMessageFromDict(response))

    def onLogin(self, connection, decoded_request):
        if('username' not in decoded_request):
            raise InvalidRequestError("key 'username' not found.")
        username = decoded_request['username']
        
        if('password' not in decoded_request):
            raise InvalidRequestError("key 'password' not found.")
        password = decoded_request['password']

        dao = UserDAO.getInstance()
        if(dao.existUser(username) == False):
            raise RequestFailedError('Username does not exist.')

        if(dao.getPassword(username) != password):
            raise RequestFailedError('Wrong password.')

        user = User(username, connection)
        self._online_users.append(user)
        user.setLoginTime(datetime.now())
        connection['user'] = user
        TN_INFO(username + " logged in.")
        response = {'code' : Code.SUCCESS}
        response['message'] = 'Successfully login.'
        response['online_time'] = dao.getOnlineTime(username)
        connection.send(Protocol.makeMessageFromDict(response))

    def onBroadcast(self, connection, decoded_request):
        if('user' not in connection.userData()):
            raise RequestFailedError('You must log in before sending message.')
        user = connection['user']

        if('message' not in decoded_request):
            raise InvalidRequestError("key 'message' not found.")
        message = decoded_request['message']

        # send response
        response = {'code' : Code.SUCCESS}
        connection.send(Protocol.makeMessageFromDict(response))
        
        TN_INFO(user.getName() + " broadcast a message: " + message)
        for sendto in self._online_users:
            if sendto is user:
                continue
            self.sendMessage(user, sendto, message)

    def onCreateRoom(self, connection, decoded_request):
        if 'user' not in connection.userData():
            raise RequestFailedError('You must log in before creating room.')
        user = connection['user']

        config = tryGetKey(decoded_request, 'config')
        roomname = tryGetKey(config, 'name')

        if roomname in self._rooms:
            raise RequestFailedError("Room name already exists.")

        TN_INFO(user.getName() + " creates a room: " + roomname)
        room = Room(roomname, user)
        self._rooms[roomname] = room
        self.userEnterRoom(user, room)
        response = {'code' : Code.SUCCESS}
        response['room'] = room.toDict()
        connection.send(Protocol.makeMessageFromDict(response))

    def onGetRooms(self, connection):
        if 'user' not in connection.userData():
            raise RequestFailedError('You must log in before getting rooms.')
        user = connection['user']

        response = {'code' : Code.SUCCESS}
        response['rooms'] = [room for room in self._rooms]
        connection.send(Protocol.makeMessageFromDict(response))

    def onExitRoom(self, connection):
        if 'user' not in connection.userData():
            raise RequestFailedError('You must log in before getting rooms.')
        user = connection['user']

        room = user.getRoom()
        if room is None:
            raise RequestFailedError('You are not in a room.')
        
        TN_INFO(user.getName() + " exits room " + room.getName())
        self.userExitRoom(user, room)

        response = {'code' : Code.SUCCESS}
        connection.send(Protocol.makeMessageFromDict(response))

    def onEnterRoom(self, connection, decoded_request):
        if 'user' not in connection.userData():
            raise RequestFailedError('You must log in before entering rooms.')
        user = connection['user']

        if user.getRoom() is not None:
            raise RequestFailedError('You must leave your room before entering another room.')

        roomname = tryGetKey(decoded_request, 'room')
        if roomname not in self._rooms:
            raise RequestFailedError("room '." + roomname + "' does not exist.")
        
        TN_INFO(user.getName() + " enters room " + roomname)
        room = self._rooms[roomname]
        self.userEnterRoom(user, room)

        response = {'code' : Code.SUCCESS}
        response['room'] = room.toDict()
        connection.send(Protocol.makeMessageFromDict(response))

    def onSendRoomMessage(self, connection, decoded_request):
        if 'user' not in connection.userData():
            raise RequestFailedError('You must log in first.')
        user = connection['user']

        room = user.getRoom()
        if room is None:
            raise RequestFailedError('You are not in a room.')

        message = tryGetKey(decoded_request, 'message')
        TN_INFO(user.getName() + " send a room message: " + message)

        response = {'code' : Code.SUCCESS}
        connection.send(Protocol.makeMessageFromDict(response))
        
        for sendto in room.getUsers():
            if sendto is user:
                continue
            self.sendRoomMessage(user, sendto, message)

    def logout(self, user):
        TN_INFO(user.getName() + " logged out.")
        
        room = user.getRoom()
        if room:
            self.userExitRoom(user, room)

        online_time = (datetime.now() - user.getLoginTime()).total_seconds()
        UserDAO.getInstance().addOnlineTime(user.getName(), int(online_time))
            
        self._online_users.remove(user)
        del user.getConnection()['user']
        del user

    def userEnterRoom(self, user, room):
        user.setRoom(room)
        room.addUser(user)

        self.serverBroadcastRoomMessage(room, user.getName() + " enters the room.")
        for roomuser in room.getUsers():
            connection = roomuser.getConnection()
            package = {'action': 'room_user_enter',
                'user' : user.getName()}
            connection.send(Protocol.makeMessageFromDict(package))

    def userExitRoom(self, user, room):
        room.removeUser(user)
        if len(room.getUsers()) == 0:
            TN_INFO('room ' + room.getName() + ' destroyed')
            del self._rooms[room.getName()]
        else:
            self.serverBroadcastRoomMessage(room, user.getName() + " exits the room.")
            for roomuser in room.getUsers():
                connection = roomuser.getConnection()
                package = {'action': 'room_user_exit',
                    'user' : user.getName()}
                connection.send(Protocol.makeMessageFromDict(package))
        user.setRoom(None)

    def sendMessage(self, sendfrom, sendto, message):
        connection = sendto.getConnection()
        package = {'action': 'broadcast',
            'from' : sendfrom.getName(), 
            'message' : message}
        connection.send(Protocol.makeMessageFromDict(package))

    def sendRoomMessage(self, sendfrom, sendto, message):
        connection = sendto.getConnection()
        package = {'action': 'room_receive_message',
            'from' : sendfrom.getName(), 
            'message' : message}
        connection.send(Protocol.makeMessageFromDict(package))

    def serverBroadcastRoomMessage(self, room, message):
        for user in room.getUsers():
            connection = user.getConnection()
            package = {'action': 'room_server_broadcast',
                'message' : message}
            connection.send(Protocol.makeMessageFromDict(package))

if __name__ == '__main__':
    event_dispatcher = EventDispatcher()
    event_dispatcher.getPoller().setMaxTimeout(50)
    server = MainServer(event_dispatcher, ('0.0.0.0', 2500))
    server.start()
    event_dispatcher.run()