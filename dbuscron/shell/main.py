import os, sys

def run():

    from dbuscron import Logger, OptionsParser

    options = OptionsParser(
            daemon=dict(names=('-f', '--nodaemon'), action='store_false', default=True),
            quiet=dict(names=('--quiet', '-q'), action='count', default=0),
            verbose=dict(names=('--verbose', '-v'), action='count', default=0),
            config=dict(names=('--conf', '--config', '-c'), default='/etc/dbuscrontab'),
            logfile=dict(names=('--log', '--logfile', '-l')),
            userid=dict(names=('-u', '--user', '--uid', '--userid')),
            groupid=dict(names=('-g', '--group', '--gid', '--groupid')))

    logout = sys.stderr
    if options.logfile:
        logout = open(options.logfile, 'wb')

    log = Logger(__name__, out=logout)
    log.level = options.verbose - options.quiet + Logger.WARNING

    if options.userid or options.groupid:
        from dbuscron.util import set_user_and_group
        set_user_and_group(options.userid, options.groupid)

    if options.daemon:
        from dbuscron.util import daemonize
        daemonize(
            pidfile='/var/run/dbuscron.pid',
            logfile='/var/log/dbuscron.log'
            )

    from dbuscron import DbusBus, DbusRule, Command, Commands, CrontabParser

    bus = DbusBus()
    commands = Commands()

    crontab = CrontabParser(options.config)

    def load_config(parser):
        for rule, cmd in parser:
            matcher = DbusRule(**rule)
            command = Command(cmd)
            matcher.register()
            log('rule parsed', matcher, command)
            commands.add(matcher, command)

    load_config(crontab)

    def reload_config_on_signal(sig_no, stack):
        log('Signal #%d received: reloading config...' % (sig_no))
        commands.clear()
        load_config(crontab)
        log('Done config reloading.')

    import signal
    signal.signal(signal.SIGHUP, reload_config_on_signal)

    commands.environ = crontab.environ
    bus.attach_handler(commands.handler)

    try:
        bus.listen()
    except KeyboardInterrupt:
        sys.exit(2)

