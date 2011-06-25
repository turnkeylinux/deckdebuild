import sys
import getopt
import copy

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

class BoolOpt(Opt):
    pass

def is_bool(opt):
    return isinstance(opt, BoolOpt)

class Opts:
    def __init__(self):
        # make copies of options
        attrnames =  [ attrname for attrname in vars(self.__class__) 
                       if attrname[0] != "_" ]

        for attrname in attrnames:
            attr = copy.copy(getattr(self, attrname))
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
    @classmethod
    def getopt(cls, args=None):
        # make arguments for getopt.gnu_getopt
        longopts = []
        shortopts = ""

        opts = cls.Opts()
        for opt in opts:
            longopt = opt.name
            shortopt = opt.short

            if not is_bool(opt):
                longopt += "="

                if shortopt:
                    shortopt += ":"

            longopts.append(longopt)
            shortopts += shortopt

        if not args:
            args = sys.argv[1:]
                
        cli_opts, args = getopt.gnu_getopt(args, shortopts, longopts)
        for cli_opt, cli_val in cli_opts:
            for opt in opts:
                if cli_opt in ("--" + opt.name, "-" + opt.short):
                    if is_bool(opt):
                        opt.val = True
                    else:
                        opt.val = cli_val

        return opts, args

class TestOpts(Opts):
    bool = BoolOpt(short="b", default=False)
    val = Opt(short="v")

class TestCliConf(CliConf):
    __doc__ = __doc__

    Opts = TestOpts
    name = "test"

def test():
    opts, args = TestCliConf.getopt()

    print `args`
    print `opts`
    for opt in opts:
        print "%s - %s " % (opt.name, dict(opt))

    #TestCliConf.usage()

if __name__ == "__main__":
    test()

