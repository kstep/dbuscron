
import os
from dbuscron.bus import get_dbus_message_type

class Command(object):
    def __init__(self, cmd):
        self.__value = cmd
        if self.is_shell_cmd:
            self.__file = os.environ.get('SHELL', '/bin/sh')
            self.__args = [self.__file, '-c', self.__value]
        else:
            self.__args = cmd.split(' ')
            self.__file = self.__args[0]

    def __call__(self, bus, message, environ):
        args_list = message.get_args_list()
        env = dict()
        env.update(environ)
        env.update(dict(
                (('DBUS_ARG%d' % i, str(args_list[i])) for i in range(0, len(args_list))),
                DBUS_ARGN   = str(len(args_list)),
                DBUS_SENDER = str(message.get_sender()),
                DBUS_DEST   = str(message.get_destination()),
                DBUS_IFACE  = str(message.get_interface()),
                DBUS_PATH   = str(message.get_path()),
                DBUS_MEMBER = str(message.get_member()),
                DBUS_BUS    = bus.__class__.__name__.lower()[0:-3],
                DBUS_TYPE   = get_dbus_message_type(message)
                ))
        result = os.spawnvpe(os.P_WAIT, self.__file, self.__args, env)
        return result

    @property
    def is_shell_cmd(self):
        for c in '|><$&;{}':
            if c in self.__value:
                return True
        return False

    def __str__(self):
        return self.__value

class Commands(object):
    __commands = {}
    __environ = {}

    def _get_environ(self):
        return self.__environ

    def _set_environ(self, value):
        self.__environ = dict()
        self.__environ.update(os.environ)
        self.__environ.update(value)

    environ = property(_get_environ, _set_environ)

    def handler(self, bus, message):
        for rule, command in self.__commands.iteritems():
            if rule.match(bus, message):
                command(bus, message, self.__environ)
                return

    def add(self, matcher, command):
        self.__commands[matcher] = command

