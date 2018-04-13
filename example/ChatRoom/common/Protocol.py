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
    def makeMessageFromDict(d):
        return dumps(d)

    @staticmethod
    def isResponse(message):
        json_obj = loads(message)
        return 'action' not in json_obj




