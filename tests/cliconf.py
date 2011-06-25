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
        progname = "myprog"

    opts, args = MyCliConf.getopt()
    for opt in opts:
        print "%s=%s" % (opt.name, opt.val)
"""

import os
import sys
import getopt
import copy
import types

class Opt:
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
    pass

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

class CliConf:
    @staticmethod
    def parse_bool(val):
        if val.lower() in ('', '0', 'no', 'false'):
            return False

        if val.lower() in ('1', 'yes', 'true'):
            return True

        return None

    @classmethod
    def getopt(cls, args=None):
        # make arguments for getopt.gnu_getopt
        longopts = []
        shortopts = ""

        opts = cls.Opts()
        for opt in opts:
            longopt = opt.longopt
            shortopt = opt.short

            if not is_bool(opt):
                longopt += "="

                if shortopt:
                    shortopt += ":"

            longopts.append(longopt)
            shortopts += shortopt

        if not args:
            args = sys.argv[1:]
                
        for opt in opts:
            optenv = cls.progname + "_" + opt.name
            optenv = optenv.upper()

            if optenv not in os.environ:
                continue

            val = os.environ[optenv]

            if is_bool(opt):
                val = cls.parse_bool(val)

            opt.val = val

        cli_opts, args = getopt.gnu_getopt(args, shortopts, longopts)
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
    progname = "test"

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

