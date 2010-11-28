#!/usr/bin/python
#
# bus type sender interface path member destination args command
#
# Examples for N900:
#
# Headphones unplugged:
# S signal * org.freedesktop.Hal.Manager /org/freedesktop/Hal/Manager DeviceRemoved * * echo Headphones unplugged;
#
# Call recieved:
# S signal * com.nokia.csd.Call /com/nokia/csd/call Coming * * echo $DBUS_ARG1 is calling
#

import sys

if __name__ == '__main__':

    from dbuscron import Logger, OptionsParser

    options = OptionsParser('fvc:l:')
    daemon = not options.f

    logout = sys.stderr
    if options.l:
        logout = open(options.l, 'wb')

    log = Logger(__name__, out=logout)
    log.level = options.v + Logger.ERROR

    if daemon:
        from dbuscron.daemonize import daemonize
        daemonize(
            pidfile='/var/run/dbuscron.pid',
            logfile='/var/log/dbuscron.log'
            )

    from dbuscron import DbusBus, DbusRule, Command, Commands, CrontabParser

    bus = DbusBus()
    commands = Commands()
    crontab = CrontabParser(options.c or '/etc/dbuscrontab')

    for rule, cmd in crontab:
        matcher = DbusRule(**rule)
        command = Command(cmd)
        matcher.register()
        log.info('%s %s' % (matcher, command))
        commands.add(matcher, command)

    commands.environ = crontab.environ
    bus.attach_handler(commands.handler)

    try:
        bus.listen()
    except KeyboardInterrupt:
        sys.exit(2)

# vim: ts=8 sts=4 sw=4 et

