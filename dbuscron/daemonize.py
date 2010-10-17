import os, sys

def daemonize(logfile=None, errfile=None, pidfile=None):
    devnull = os.devnull if hasattr(os, 'devnull') else '/dev/null'

    initwd = os.getcwd()
    def absolutize(path):
        if path.startswith('/'):
            return path
        return os.path.join(initwd, path)

    try:
        if os.fork() == 0:
            os.setsid()
            if os.fork() == 0:
                os.chdir('/')
                os.umask(0)
            else:
                os._exit(0)
        else:
            os._exit(0)
    except OSError, e:
        raise Exception('Failed daemonization: %s' % str(e))

    for i in range(0, 3):
        os.close(i)

    os.open(devnull, os.O_RDWR)

    def open_trunc(fname):
        f = os.open(fname, \
            os.O_WRONLY|os.O_CREAT)
        os.ftruncate(f, 0)
        return f

    def open_or_dup(fname, fd=None):
        if fname:
            return open_trunc(absolutize(fname))
        elif fd:
            os.dup2(*fd)

    open_or_dup(logfile, (0, 1))
    open_or_dup(errfile, (1, 2))

    pid = os.getpid()
    if pidfile:
        pidfile = absolutize(pidfile)
        fd = open_trunc(pidfile)
        os.write(fd, str(pid))
        os.close(fd)

        def remove_pidfile():
            os.unlink(pidfile)
        sys.exitfunc = remove_pidfile

    return pid

