class ErrorLevel:  
    FATAL = 1
    ERROR = 2
    WARNING = 3
    INFO = 4
    DEBUG = 5
    TRACE = 6

class TinyNetError(Exception):
    def __init__(self, message, code=None, level=ErrorLevel.ERROR):
        super(TinyNetError, self).__init__(message)
        self._code = code

class ConnectionClosedError(Exception):
    pass


