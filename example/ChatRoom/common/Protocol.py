from json import loads, dumps
from struct import pack, pack_into

class Code:
    SUCCESS = 100
    INVALID_REQUEST = 200
    INTERNAL_ERROR = 201
    REQUEST_FAILED = 202
    UNKNOWN_ERROR = 999

class Protocol:
    @staticmethod
    def makeMessage(data):
        utf8data = data.encode('utf-8')
        length = len(utf8data)
        message = bytearray(length + 4)
        pack_into("!l", message, 0, length) # write length into message in network order
        pack_into("!" + str(length) + "s", message, 4, utf8data) # write utf8data into message 
        return message

    @staticmethod
    def makeMessageFromDict(d):
        return Protocol.makeMessage(dumps(d))

    @staticmethod
    def isResponse(message):
        json_obj = loads(message)
        return 'action' not in json_obj




