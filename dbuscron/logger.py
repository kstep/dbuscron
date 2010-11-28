
import sys
from datetime import datetime

class Logger(object):

    __level = 1
    __out = None
    __name = None

    DEBUG = 4
    INFO = 3
    WARNING = 2
    ERROR = 1
    PANIC = 0

    def __init__(self, name, out=sys.stderr):
        self.__out = out
        self.__name = name

    def _get_level(self):
        return self.__level
    def _set_level(self, value):
        self.__level = int(value)
    level = property(_get_level, _set_level)

    def log(self, level, message):
        if level <= self.__level:
            ts = datetime.now().strftime('%Y-%m-%d %H:%M')
            self.__out.write('[%s] %s\n' % (ts, message))

    def debug(self, message):
        self.log(self.DEBUG, message)
    
    def info(self, message):
        self.log(self.INFO, message)
    
    def warn(self, message):
        self.log(self.WARNING, message)

    def error(self, message):
        self.log(self.ERROR, message)

    def panic(self, message):
        self.log(self.PANIC, message)
