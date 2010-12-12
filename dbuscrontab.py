#!/usr/bin/python

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

def get_dbuscron_pid():
    try:
        f = os.popen('initctl status dbuscron', 'r')
        status = f.readline()
        f.close()
        return int(status.strip().split(' ').pop())
    except:
        raise SystemError('Unable to get PID of dbuscron job.')

def check_syntax(filename):
    parser = CrontabParser(filename)
    for rule, command in parser:
        pass

if __name__ == '__main__':

    try:
        action = sys.argv[1]
    except IndexError:
        action = None

    if action == '-e':
        # 1. create temporary config file copy
        temp_file = create_temp_file(conffile)
        mod_time = os.path.getmtime(temp_file)

        # 2. run system editor on this file
        run_system_editor(temp_file)

        # 3. check if this file is changed
        if os.path.getmtime(temp_file) <= mod_time:
            print 'File was not changed.'
            sys.exit(2)

        # TODO: 4. check this file's syntax
        try:
            check_syntax(temp_file)
        except CrontabParserError, e:
            print e.message
            print 'File has syntax errors, aborting.'
            sys.exit(3)

        # 5. replace system wide config file with new one
        shutil.move(temp_file, conffile)

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
        try:
            check_syntax(conffile)
        except CrontabParserError, e:
            print e.message
            print "File %s has syntax errors." % (conffile)
            sys.exit(3)
        print "File %s has no syntax errors." % (conffile)

    else:
        print """
Usage:
    %(myname)s { -e | -l }

    -e      edit %(conffile)s file
    -l      list contents of %(conffile)s file
    -k      check %(conffile)s's syntax

""" % dict(myname=os.path.basename(sys.argv[0]), conffile=conffile)

