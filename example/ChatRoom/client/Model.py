

class User(object):
    def __init__(self, name):
        self._name = name
        self._online_time = 0
        self._room = None

    def getName(self):
        return self._name

    def getOnlineTime(self):
        return self._online_time

    def setRoom(self, room):
        self._room = room

    def getRoom(self):
        return self._room

class RoomConfig(object):
    MAX_NAME_LENGTH = 16

    def setName(self, name):
        self._name = name

    def getName(self):
        return self._name

    def toDict(self):
        d = {}
        d['name'] = self._name
        return d

class Room(object):
    def __init__(self):
        self._userList = []

    def setName(self, name):
        self._name = name

    def getName(self):
        return self._name

    def getUserList(self):
        return self._userList

    def addUser(self, username):
        self._userList.append(username)

    def removeUser(self, username):
        self._userList.remove(username)
        