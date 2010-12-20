# encoding: utf-8
from __future__ import with_statement
import re
from dbuscron.bus import DbusBus

def unescape(value):
    if not value or r'\x' not in value:
        return value

    r = re.compile(r'\\x([0-9A-Fa-f]{2})')
    return r.sub(lambda m: chr(int(m.group(1), 16)), value)

def product(*args):
    if args:
        head, tail = args[0], args[1:]
        for h in head:
            for t in product(*tail):
                yield (h,) + t

    else:
        yield ()

class CrontabParserError(SyntaxError):
    def __init__(self, message, lineno, expected=None):
        if expected:
            if isinstance(expected, (tuple, list)):
                exp = ' (expected %s or %s)' % (', '.join(expected[:-1]), expected[-1])
        else:
            exp = ''

        msg = '%s%s at line %d' % (message, exp, lineno)

        SyntaxError.__init__(self, msg)

class CrontabParser(object):
    __fields_sep = re.compile(r'\s+')
    __envvar_sep = re.compile(r'\s*=\s*')
    __fields_chk = {
            'bus_'         : None,
            'type_'        : ('signal','method_call','method_return','error'),
            'sender_'      : None,
            'interface_'   : re.compile(r'^[a-zA-Z][a-zA-Z0-9_.]+$'),
            'path_'        : re.compile(r'^/[a-zA-Z0-9_/]+$'),
            'member_'      : re.compile(r'^[a-zA-Z][a-zA-Z0-9_]+$'),
            'destination_' : None,
            'args_'        : None,
            }
    __fields = [
            'bus_',
            'type_',
            'sender_',
            'interface_',
            'path_',
            'member_',
            'destination_',
            'args_',
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
                    parts = self.__envvar_sep.split(line, 1)
                    if len(parts) == 2:
                        self.__environ[parts[0]] = parts[1]
                        continue

                    raise CrontabParserError('Unexpected number of records', lineno)

                rule = [('s','S'), self.__fields_chk['type_'], (None,), (None,), (None,), (None,), (None,), (None,)]

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
                        raise CrontabParserError('Unexpected bus value', lineno, expected=('S', 's', '*'))

                    if r[7]:
                        r[7] = map(unescape, r[7].split(';'))

                    ruled = dict()
                    for i, f in enumerate(self.__fields):
                        if r[i] is not None and self.__fields_chk[f]:
                            if isinstance(self.__fields_chk[f], tuple):
                                if r[i] not in self.__fields_chk[f]:
                                    raise CrontabParserError('Unexpected %s value' % (f.strip('_')), lineno,
                                            expected=self.__fields_chk[f])
                            else:
                                if not self.__fields_chk[f].match(r[i]):
                                    raise CrontabParserError('Incorrect %s value' % (f.strip('_')), lineno)
                        ruled[f] = r[i]

                    yield ruled, command

def OptionsParser(args=None, help=u'', **opts):

    from optparse import OptionParser
    import dbuscron
    parser = OptionParser(usage=help, version="%prog "+dbuscron.__version__)
    for opt, desc in opts.iteritems():
        names = desc.pop('names')
        desc['dest'] = opt
        parser.add_option(*names, **desc)

    return parser.parse_args(args)[0]

