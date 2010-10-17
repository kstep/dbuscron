from __future__ import with_statement
import re
from dbuscron.bus import DbusBus

try:
    from itertools import product
except ImportError:
    def product(*args):
        if args:
            head, tail = args[0], args[1:]
            for h in head:
                for t in product(*tail):
                    yield (h,) + t
    
        else:
            yield ()

class CrontabParser(object):
    __fields_sep = re.compile(r'\s+')
    __envvar_sep = re.compile(r'\s*=\s*')
    __fields = [
            'bus_',
            'type_',
            'sender_',
            'interface_',
            'path_',
            'member_',
            'destination_',
            'args_',
            #'command'
            ]

    def __init__(self, fname):
        self.__bus = DbusBus()
        self.__filename = fname
        self.__environ = dict()

    @property
    def environ(self):
        return self.__environ

    def __iter__(self):
        # bus type sender interface path member destination args command
        with open(self.__filename) as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith('#'):
                    continue

                parts = self.__fields_sep.split(line, 8)
                if len(parts) < 9:
                    parts = self.__envvar_sep(line, 1)
                    if len(parts) == 2:
                        self.__environ[parts[0]] = parts[1]
                    continue

                rule = [(None,), (None,), (None,), (None,), (None,), (None,), (None,), (None,)]

                for p in range(1, 8):
                    if parts[p] != '*':
                        rule[p] = parts[p].split(',')

                command = parts[8]

                if parts[0] == '*' or parts[0] == 'S,s' or parts[0] == 's,S':
                    rule[0] = (self.__bus.system, self.__bus.session)
                elif parts[0] == 's':
                    rule[0] = (self.__bus.session,)
                elif parts[0] == 'S':
                    rule[0] = (self.__bus.system,)
                    
                for r in product(*rule):
                    if r[7]:
                        r[7] = r[7].split(';')
                    ruled = dict()
                    for i, f in enumerate(self.__fields):
                        ruled[f] = r[i]
                    yield ruled, command

