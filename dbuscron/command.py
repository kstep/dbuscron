# encoding: utf-8

import os
from dbuscron.bus import get_dbus_message_type, dbus_to_str
from dbuscron.logger import Logger
log = Logger(__name__)

class Command(object):
    def __init__(self, cmd):
        self.__value = cmd
        self.__auto_args = False
        if self.is_shell_cmd:
            self.__file = os.environ.get('SHELL', '/bin/sh')
            self.__args = [self.__file, '-c', self.__value]
        else:
            self.__args = cmd.split(' ')
            self.__file = self.__args[0]
            if len(self.__args) == 1 \
                and self.__file.startswith('!'):
                self.__file = self.__file.lstrip('!')
                self.__auto_args = True

    def __call__(self, bus, message, environ):
        args_list = map(dbus_to_str, message.get_args_list())
        env = dict()
        env.update(environ)
        try:
            dbus_env = dict(
                    (('DBUS_ARG%d' % i, a) for i, a in enumerate(args_list)),
                    DBUS_ARGN   = str(len(args_list)),
                    DBUS_SENDER = str(message.get_sender() or ''),
                    DBUS_DEST   = str(message.get_destination() or ''),
                    DBUS_IFACE  = str(message.get_interface() or ''),
                    DBUS_PATH   = str(message.get_path() or ''),
                    DBUS_MEMBER = str(message.get_member() or ''),
                    DBUS_BUS    = bus.__class__.__name__.lower()[0:-3],
                    DBUS_ERROR  = str(message.get_error_name() or ''),
                    DBUS_TYPE   = get_dbus_message_type(message)
                    )
            env.update(dbus_env)
        except Exception, e:
            log.error('environ exception', e)
            raise e

        if self.__auto_args:
            if dbus_env['DBUS_TYPE'] in ('signal', 'method_call'):
                args_list[0:0] = [
                    dbus_env['DBUS_IFACE'],
                    dbus_env['DBUS_MEMBER']]
            elif dbus_env['DBUS_TYPE'] == 'error':
               args_list.insert(0, dbus_env['DBUS_ERROR'])

            args_list[0:0] = [
                    self.__file,
                    dbus_env['DBUS_SENDER'],
                    dbus_env['DBUS_DEST']]
        else:
            args_list = self.__args

        result = os.spawnvpe(os.P_WAIT, self.__file, args_list, env)
        if result != 0:
            log.warn('command returned non-zero status', self.__file, args_list, dbus_env, result)
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

    def __iter__(self):
        for m, c in self.__commands.iteritems():
            yield m, c

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
                log('rule matched', rule, command)
                command(bus, message, self.__environ)
                return

    def add(self, matcher, command):
        self.__commands[matcher] = command

    def clear(self):
        self.__commands = {}

