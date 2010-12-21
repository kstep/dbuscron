
def run():

    # 1. parse arguments
    from dbuscron.parser import OptionsParser
    options = OptionsParser(
            daemon=dict(names=('-f', '--nodaemon'), action='store_false', default=True),
            quiet=dict(names=('--quiet', '-q'), action='count', default=0),
            verbose=dict(names=('--verbose', '-v'), action='count', default=0),
            config=dict(names=('--conf', '--config', '-c'), default='/etc/dbuscrontab'),
            logfile=dict(names=('--log', '--logfile', '-l')),
            userid=dict(names=('-u', '--user', '--uid', '--userid')),
            groupid=dict(names=('-g', '--group', '--gid', '--groupid')),
            sessionaddr=dict(names=('-s', '--session', '--sessionaddr')))

    # 2. logging setup
    import sys
    logout = sys.stderr
    if options.logfile:
        logout = open(options.logfile, 'wb')

    from dbuscron.logger import Logger
    log = Logger(__name__, out=logout)
    log.level = options.verbose - options.quiet + Logger.WARNING

    # 3. process properties setup
    try:
        if options.userid or options.groupid:
            from dbuscron.util import set_user_and_group
            set_user_and_group(options.userid, options.groupid)

        if options.daemon:
            from dbuscron.util import daemonize
            daemonize(
                pidfile='/var/run/dbuscron.pid',
                logfile='/var/log/dbuscron.log')

    except SystemError, e:
        log.error(e.message)
        sys.exit(4)

    # 4. main instances initialization
    from dbuscron.bus import DbusBus, DbusRule
    from dbuscron.command import Command, Commands
    from dbuscron.parser import CrontabParser, CrontabParserError

    bus = DbusBus(options.sessionaddr)
    commands = Commands()

    config_files = [ options.config ]
    if not options.config.endswith('.d'):
        config_files.insert(0, options.config+'.d')
    crontab = CrontabParser(*config_files)

    # 5. load config file
    def load_config(parser):
        log("Loading config from", parser.filename, "...")
        try:
            for rule, cmd in parser:
                matcher = DbusRule(**rule)
                command = Command(cmd)
                matcher.register()
                log('rule parsed', matcher, command)
                commands.add(matcher, command)

            commands.environ = parser.environ

        except CrontabParserError, e:
            log.error(e.message)
            sys.exit(3)

    load_config(crontab)

    # 6. setup signal handlers
    def reload_config_on_signal(sig_no, stack):
        log('Signal #%d received: reloading config...' % (sig_no))
        commands.clear()
        load_config(crontab)
        log('Done config reloading.')

    import signal
    signal.signal(signal.SIGHUP, reload_config_on_signal)

    # 7. setup DBUS handlers
    bus.attach_handler(commands.handler)

    # 8. run main application listen loop
    try:
        bus.listen()
    except KeyboardInterrupt:
        sys.exit(2)

