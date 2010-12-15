from __future__ import with_statement

import dbus, os

from dbuscron.logger import Logger
log = Logger(__name__)

def dbus_to_str(value):
    try:
        if isinstance(value, dbus.Byte):
            result = str(int(value))
        elif isinstance(value, dbus.ByteArray):
            result = ','.join(str(ord(v)) for v in value)
        elif isinstance(value, dbus.Array):
            result = ','.join(dbus_to_str(v) for v in value)
        elif isinstance(value, dbus.Dictionary):
            result = ','.join('%s:%s' % (k, dbus_to_str(v)) for k, v in value.iteritems())
        elif isinstance(value, dbus.String):
            result = value.encode('utf-8')
        else:
            result = str(value)
        return result
    except Exception, e:
        log.error('convert exception', e)
        raise e


def get_dbus_message_type(message):
    result = message.__class__.__name__[0:-7]
    for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        result = result.replace(c, '_'+c.lower())
    return result.strip('_')

class DbusBus(object):
    __bus = None
    __system_bus = None
    __session_bus = None

    def __new__(cls):
        if not cls.__bus:
            cls.__bus = super(DbusBus, cls).__new__(cls)
        return cls.__bus

    def __init__(self):
        self.get_session_bus_address()
        from dbus.mainloop.glib import DBusGMainLoop
        DBusGMainLoop(set_as_default=True)

    def get_session_bus_address(self):
        try:
            return os.environ['DBUS_SESSION_BUS_ADDRESS']
        except KeyError:
            with open('/tmp/session_bus_address.user', 'rb') as f:
                session_bus_address = f.readline().strip().split('=', 1).pop().strip("'\"")
                os.environ['DBUS_SESSION_BUS_ADDRESS'] = session_bus_address
                log('session bus address aquired', session_bus_address)
                return session_bus_address

    @property
    def system(self):
        if not self.__system_bus:
            self.__system_bus = dbus.SystemBus()
        return self.__system_bus

    @property
    def session(self):
        if not self.__session_bus:
            self.__session_bus = dbus.SessionBus()
        return self.__session_bus

    def attach_handler(self, handler):
        if self.__system_bus:
            self.__system_bus.add_message_filter(handler)
        if self.__session_bus:
            self.__session_bus.add_message_filter(handler)
    def listen(self):
        from gobject import MainLoop
        loop = MainLoop()
        loop.run()

class DbusRule(object):
    def __init__(self, bus_=None, type_=None, sender_=None, interface_=None, path_=None, member_=None, destination_=None, args_=[]):
        self._bus         = bus_
        self._type        = type_
        self._sender      = sender_
        self._interface   = interface_
        self._path        = path_
        self._member      = member_
        self._destination = destination_
        self._args        = args_

    def register(self):
        rule = str(self)
        if rule:
            self._bus.add_match_string(rule)

    def unregister(self):
        rule = str(self)
        if rule:
            self._bus.remove_match_string(rule)

    def __del__(self):
       self.unregister()

    def __str__(self):
        rule = []
        for key in ['type', 'sender', 'interface', 'path', 'member', 'destination']:
            value = getattr(self, '_'+key)
            if value is not None:
                rule.append("%s='%s'" % (key, value))

        if self._args:
            for i, arg in enumerate(self._args):
                rule.append("arg%d%s='%s'" % (i, 'path' if arg.startswith('/') else '', arg))

        return ','.join(rule)

    def match(self, bus, message):

        if self._bus not in (None, bus):
            return False

        if self._type is not None:
            type_ = get_dbus_message_type(message)
            if self._type != type_:
                return False

        if self._sender not in (None, message.get_sender()):
            return False

        if self._interface not in (None, message.get_interface()):
            return False

        if self._path not in (None, message.get_path()):
            return False

        if self._member not in (None, message.get_member()):
            return False

        if self._destination not in (None, message.get_destination()):
            return False

        if self._args is not None:
            args_ = message.get_args_list()
            for i, arg in enumerate(args_):
                if i >= len(self._args):
                    break
                if self._args[i] not in (None, str(arg)):
                    return False

        return True

