"""Pythonic cli configuration module

Usage::

    from cliconf import *
    class MyOpts(Opts):

        myopt = Opt(short="o")
        mybool = BoolOpt(short="b")

        simple_opt = ""
        simple_bool = False

    class MyCliConf(CliConf):
        Opts = MyOpts
        env_path = "MYPROG_"
        file_path = "/etc/myprog.conf"

    opts, args = MyCliConf.getopt()
    for opt in opts:
        print "%s=%s" % (opt.name, opt.val)
"""

import os
import sys
import getopt
import copy
import types
import re

class Opt(object):
    def __init__(self, desc=None, short="", rootonly=False, default=None):
        self.desc = desc
        self.short = short
        self.rootonly = rootonly

        self.val = default
        self.name = None

    def __iter__(self):
        for attrname, attr in vars(self).items():
            yield attrname, attr

    def longopt(self):
        if self.name:
            return self.name.replace("_", "-")

        return ""
    longopt = property(longopt)

class BoolOpt(Opt):
    @staticmethod
    def parse_bool(val):
        if val.lower() in ('', '0', 'no', 'false'):
            return False

        if val.lower() in ('1', 'yes', 'true'):
            return True

        raise Error("illegal value for bool (%s)" % val)

    def set_val(self, val):
        if val not in (None, True, False):
            val = self.parse_bool(str(val))
            
        self._val = val

    def get_val(self):
        if hasattr(self, '_val'):
            return self._val

        return None

    val = property(get_val, set_val)

def is_bool(opt):
    return isinstance(opt, BoolOpt)

class Opts:
    def __init__(self):
        # make copies of options
        for attrname, attr in vars(self.__class__).items():
            if attrname[0] == "_":
                continue

            if isinstance(attr, Opt):
                attr = copy.copy(attr)
            elif isinstance(attr, types.BooleanType):
                attr = BoolOpt(default=attr)
            else:
                attr = Opt(default=attr)

            attr.name = attrname
            setattr(self, attrname, attr)


    def __iter__(self):
        for attr in vars(self).values():
            if isinstance(attr, Opt):
                yield attr

    def __getitem__(self, attrname):
        attr = getattr(self, attrname)
        if isinstance(attr, Opt):
            return attr

        raise KeyError(`attrname`)

    def __contains__(self, opt):
        if isinstance(opt, Opt):
            return opt in list(self)

        if isinstance(opt, types.StringType):
            attr = getattr(self, opt, None)
            if isinstance(attr, Opt):
                return True
            return False

        raise TypeError("type(%s) not a string or an Opt instance" %
                        `opt`)

class Error(Exception):
    pass

class CliConf:
    env_path = None
    file_path = None

    @staticmethod
    def _cli_getopt(args, opts):
        # make arguments for getopt.gnu_getopt
        longopts = []
        shortopts = ""

        for opt in opts:
            longopt = opt.longopt
            shortopt = opt.short

            if not is_bool(opt):
                longopt += "="

                if shortopt:
                    shortopt += ":"

            longopts.append(longopt)
            shortopts += shortopt

        return getopt.gnu_getopt(args, shortopts, longopts)

    @staticmethod
    def _parse_conf_file(path):
        try:
            fh = file(path)

            for line in fh.readlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                name, val = re.split(r'\s+', line)
                yield name, val
        except IOError:
            pass
    
    @classmethod
    def getopt(cls, args=None):
        opts = cls.Opts()

        if cls.file_path:
            for name, val in cls._parse_conf_file(cls.file_path):
                name = name.replace("-", "_")

                if name not in opts:
                    raise Error("unknown configuration file option `%s'" %
                                name)

                opts[name].val = val

        # set options that are set in the environment
        if cls.env_path is not None:
            for opt in opts:
                optenv = cls.env_path + opt.name
                optenv = optenv.upper()

                if optenv not in os.environ:
                    continue

                opt.val = os.environ[optenv]

        if not args:
            args = sys.argv[1:]
                
        cli_opts, args = cls._cli_getopt(args, opts)
        for cli_opt, cli_val in cli_opts:
            for opt in opts:
                if cli_opt in ("--" + opt.longopt,
                               "-" + opt.short):

                    if is_bool(opt):
                        opt.val = True
                    else:
                        opt.val = cli_val

        return opts, args

class TestOpts(Opts):
    bool = BoolOpt(short="b", default=False)
    val = Opt(short="v")
    a_b = Opt()

    simple = "test"
    simplebool = False

class TestCliConf(CliConf):
    __doc__ = __doc__

    Opts = TestOpts

    env_path = "TEST_"
    file_path = "test.conf"

def test():
    import pprint
    pp = pprint.PrettyPrinter()

    opts, args = TestCliConf.getopt()

    pp.pprint([ dict(opt) for opt in opts])

    for opt in opts:
        print "%s=%s" % (opt.name, opt.val)

    print "args = " + `args`

    #TestCliConf.usage()

if __name__ == "__main__":
    test()

