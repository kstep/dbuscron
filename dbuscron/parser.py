from __future__ import with_statement
import re
from dbuscron.bus import DbusBus

def product(*args):
    if args:
        head, tail = args[0], args[1:]
        for h in head:
            for t in product(*tail):
                yield (h,) + t

    else:
        yield ()

class CrontabParserError(SyntaxError):
    pass

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
        lineno = 0
        with open(self.__filename) as f:
            for line in f:
                lineno += 1
                line = line.strip()

                if not line or line.startswith('#'):
                    continue

                parts = self.__fields_sep.split(line, 8)
                if len(parts) < 9:
                    parts = self.__envvar_sep(line, 1)
                    if len(parts) == 2:
                        self.__environ[parts[0]] = parts[1]
                        continue

                    raise SyntaxError('Unexpected number of records at line #%d.' % (lineno))

                rule = [('s','S'), ('signal','method_call','method_return','error'), (None,), (None,), (None,), (None,), (None,), (None,)]

                for p in range(0, 8):
                    if parts[p] != '*':
                        rule[p] = parts[p].split(',')

                command = parts[8]
 
                for r in product(*rule):
                    r = list(r)
                    if r[0] == 'S':
                        r[0] = self.__bus.system
                    elif r[0] == 's':
                        r[0] = self.__bus.session
                    else:
                        continue
	
                    if r[7]:
                        r[7] = r[7].split(';')

                    ruled = dict()
                    for i, f in enumerate(self.__fields):
                        ruled[f] = r[i]
                    yield ruled, command

class OptionsParser(dict):
    def __init__(self, opts, args=None):
        super(OptionsParser, self).__init__()

        if args is None:
            import sys
            args = sys.argv[1:]

        from getopt import getopt
        go, _ = getopt(args, opts)

        for o, v in go:
            k = o.strip('-')
            withval = k+':' in opts

            if self.has_key(k):
                if withval:
                    if isinstance(self[k], list):
                        self[k].append(v)
                    else:
                        self[k] = [ self[k], v ]

                else:
                    self[k] += 1

            else:
                self[k] = v if withval else 1

    def __getitem__(self, k):
        if not self.has_key(k):
            return False
        return super(OptionsParser, self).__getitem__(k)

    def __getattr__(self, k):
        return self[k]

