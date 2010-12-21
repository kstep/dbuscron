#!/usr/bin/python
from __future__ import with_statement
import os, sys

if '-h' in sys.argv or '--help' in sys.argv:
    print '''
%(name)s [ dbus-scripts-dir ] [ dbuscrontab-dir ]

    Convert all files from dbus-scripts-dir from
    dbus-scripts config format to dbuscron config
    format and put them under the same names into
    dbuscrontab-dir.

    If omitted, dbus-scripts-dir defaults to
    `/etc/dbus-scripts.d', dbuscrontab-dir
    defaults to `/etc/dbuscrontab.d'.
''' % dict(name=sys.argv[0])
    os._exit(0)

try:
    dbus_scripts_dir = sys.argv[1]
except IndexError:
    dbus_scripts_dir = '/etc/dbus-scripts.d'

try:
    dbuscron_dir = sys.argv[2]
except IndexError:
    dbuscron_dir = '/etc/dbuscrontab.d'

for fn in os.listdir(dbus_scripts_dir):
    fnam = os.path.join(dbus_scripts_dir, fn)
    if not os.path.isfile(fnam):
        continue

    fout = os.path.join(dbuscron_dir, fn)
    print '%s -> %s' % (fnam, fout)

    lineno = 0
    with open(fnam, 'rb') as f:
        lineno += 1
        with open(fout, 'wb') as o:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    print >> o, line
                    continue

                parts = line.split(' ', 5)
                opts = dict()
                for i, n in enumerate(('cmd', 'src', 'dest', 'iface', 'meth', 'args')):
                    try:
                        opts[n] = parts[i]
                    except IndexError:
                        opts[n] = '*'

                opts['args'] = opts['args'].replace(' ', ';')
                skip_args = 0
                while opts['args'].startswith('*;'):
                    opts['args'] = opts['args'][2:]
                    skip_args += 1
                opts['args'] = ';'*skip_args + opts['args']

                # bus type sender interface path member destination args command
                res = 'S signal,method_call %(src)s %(iface)s * %(meth)s %(dest)s %(args)s !%(cmd)s' % opts
                print >> o, res

