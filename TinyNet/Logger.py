import thread
import inspect
from StringIO import StringIO
from time import gmtime, strftime
import sys

class LogLevel:  
    NONE = 0
    FATAL = 1
    ERROR = 2
    WARNING = 3
    INFO = 4
    DEBUG = 5
    TRACE = 6
    ALL = 7

_log_level_tag_ = [  
            "[THIS SHOULD NOT OCCUR]", 
            "[FATAL]",
            "[ERROR]",
            "[WARNING]",
            "[INFO]",
            "[DEBUG]",
            "[TRACE]",
            "[THIS SHOULD NOT OCCUR]"
        ]

def __LOG(level, message):
    caller_frame = inspect.currentframe().f_back.f_back
    (file, line, function, lines, index) = inspect.getframeinfo(caller_frame)
    Logger.getInstance().log(level, file, function, line, message)

def TN_FATAL(message):
    __LOG(LogLevel.FATAL, message)
    sys.exit()

def TN_ERROR(message):
    __LOG(LogLevel.ERROR, message)

def TN_WARNING(message):
    __LOG(LogLevel.WARNING, message)

def TN_INFO(message):
    __LOG(LogLevel.INFO, message)

def TN_DEBUG(message):
    __LOG(LogLevel.DEBUG, message)

def TN_TRACE(message):
    __LOG(LogLevel.TRACE, message)

class Logger(object):
    _instance = None
    _instance_lock = thread.allocate_lock()
    _loglevel = LogLevel.INFO

    @staticmethod
    def getInstance():
        if(Logger._instance is None):
            Logger._instance_lock.acquire()
            if(Logger._instance is None):
                Logger._instance = Logger()
            Logger._instance_lock.release()
        return Logger._instance

    def log(self, level, file, function, line, message):
        if(level <= self._loglevel):
            stream = StringIO()
            stream.write(_log_level_tag_[level])
            stream.write("  ")
            stream.write(strftime("%Y/%m/%d %H:%M:%S", gmtime()))
            stream.write("  ")
            stream.write(message)
            stream.write("  ")
            if(level <= LogLevel.WARNING):
                stream.write(file + "," + function + "," + "line " + str(line))
            print stream.getvalue()

    def setLogLevel(self, loglevel):
        self._loglevel = loglevel

