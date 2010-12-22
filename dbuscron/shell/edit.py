
import os, sys, shutil, signal, tempfile, pipes
conffile = '/etc/dbuscrontab'
pidfile = '/var/run/dbuscron.pid'

from dbuscron.parser import CrontabParser, CrontabParserError

def create_temp_file(orig_file):
    try:
        temp_file = tempfile.mktemp(prefix=os.path.basename(orig_file))
        shutil.copy(orig_file, temp_file)
        return temp_file
    except:
        raise SystemError('Unable to make copy of dbuscrontab file.')

def run_system_editor(filename):
    editor = pipes.quote(os.environ.get('EDITOR', '/usr/bin/vim'))
    if os.system(editor + ' ' + pipes.quote(filename)) != 0:
        raise SystemError('Editor returned non-zero status value.')

def get_dbuscron_pid_from_upstart():
    f = os.popen('initctl status dbuscron', 'r')
    status = f.readline()
    f.close()
    return int(status.strip().split(' ').pop())

def get_dbuscron_pid_from_pidfile():
    f = open(pidfile, 'r')
    pid = f.readline()
    f.close()
    return int(pid)

def get_dbuscron_pid():
    try:
        return get_dbuscron_pid_from_upstart()
    except:
        try:
            return get_dbuscron_pid_from_pidfile()
        except:
            raise SystemError('Unable to get PID of dbuscron job.')

def check_syntax(filename):
    parser = CrontabParser(filename)
    try:
        for rule, command in parser:
            pass
    except CrontabParserError, e:
        print e.message
        raise SystemError("File %s has syntax errors." % (filename))

def run():

    try:
        action = sys.argv[1]
    except IndexError:
        action = None

    try:
        if action == '-e':

            # 1. create temporary config file copy
            temp_file = create_temp_file(conffile)
            mod_time = os.path.getmtime(temp_file)

            try:
                # 2. run system editor on this file
                run_system_editor(temp_file)

                # 3. check if this file is changed
                if os.path.getmtime(temp_file) <= mod_time:
                    print 'File was not changed.'
                    sys.exit(2)

                # 4. check this file's syntax
                check_syntax(temp_file)

                # 5. replace system wide config file with new one
                shutil.move(temp_file, conffile)

            finally:
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass

            # 6. send sighup to dbuscron daemon
            pid = get_dbuscron_pid()
            os.kill(pid, signal.SIGHUP)

            print "Everything's OK, SIGHUP to dbuscron is sent."

        elif action == '-l':
            f = open(conffile, 'r')
            for l in f:
                print l.strip()
            f.close()

        elif action == '-k':
            check_syntax(conffile)
            print "File %s has no syntax errors." % (conffile)

        else:
            print """
Usage:
    %(myname)s { -e | -l }

    -e      edit %(conffile)s file
    -l      list contents of %(conffile)s file
    -k      check %(conffile)s's syntax

""" % dict(myname=os.path.basename(sys.argv[0]), conffile=conffile)

    except SystemError, e:
        print e.message
        sys.exit(1)

