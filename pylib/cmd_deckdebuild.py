#!/usr/bin/python
"""build a Debian package in a decked chroot

Output dir defaults to ../

Resolution order for options:
1) command line (highest precedence)
2) environment variable
3) configuration file
4) built-in default (lowest precedence)

Options:
  -p --preserve-build		don't remove build deck after build
				environment: DECKDEBUILD_PRESERVE_BUILD
				default: removed unless build fails
  	
  -u --user <username>		build username (created if it doesn't exist)
				environment: DECKDEBUILD_USER
				default: `build'

  -r --root-cmd <prog>		command used to gain root privileges
				environment: DECKDEBUILD_ROOT_CMD
				default: `fakeroot'

Privileged options (root only):

  --satisfydepends-cmd <prog>	program used to satisfy build dependencies
				environment: DECKDEBUILD_SATISFYDEPENDS_CMD
				default: /usr/lib/pbuilder/pbuilder-satisfydepends

  --vardir <path>		var data path
				environment: DECKDEBUILD_VARDIR
				default: /var/lib/deckdebuild

Configuration file (/etc/deckdebuild.conf):
  <option> <value>
	e.g.,
	  	user build
		preserve-build true

"""
import os
import re
import sys
import help
import getopt

import deckdebuild

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] /path/to/buildroot [ /path/to/output-dir ]" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def parse_bool(val):
    if val.lower() in ('', '0', 'no', 'false'):
        return False

    if val.lower() in ('1', 'yes', 'true'):
        return True

    return None

def is_suid():
    return os.getuid() != os.geteuid()

def is_privileged_option(opt):
    if opt in ('satisfydepends_cmd', 'vardir'):
        return True

    return False

OPTS = ('preserve_build', 'user', 'root_cmd', 'satisfydepends_cmd', 'vardir')    

def parse_conf_file(path="/etc/deckdebuild.conf"):
    try:
        fh = file(path)
    except IOError:
        return {}

    conf = {}
    for line in fh.readlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        opt, val = re.split(r'\s+', line)
        opt = opt.replace("-", "_")
        if opt not in OPTS:
            fatal("unknown configuration file option `%s'" % opt)
            
        if opt == 'preserve_build':
            val = parse_bool(val)

        conf[opt] = val
    
    return conf
        
def main():
    conf = parse_conf_file()
    for opt in OPTS:
        optenv = "DECKDEBUILD_" + opt.upper()

        if optenv in os.environ:
            val = os.environ[optenv]

            if is_suid() and is_privileged_option(opt):
                continue
            
            if opt == 'preserve_build':
                val = parse_bool(val)
                if val is None:
                    fatal("invalid environment value %s=%s" % (optenv, os.environ[optenv]))

            conf[opt] = val

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'pu:r:', ['preserve-build',
                                                           'user=',
                                                           'root-cmd=',
                                                           'satisfydepends-cmd=',
                                                           'vardir='])
    except getopt.GetoptError, e:
        usage(e)

    shortsmap = { '-p': '--preserve-build',
                  '-u': '--user',
                  '-r': '--root-cmd' }
                
    for opt, val in opts:
        if opt == '-h':
            usage()

        # transform empty arguments to true
        if val == '': 
            val = True

        if is_suid() and is_privileged_option(opt[2:].replace("-", "_")):
            fatal("privileged options not allowed while running suid (must run as root)")
            
        if not opt.startswith("--"):
            opt = shortsmap[opt]

        opt = opt[2:].replace("-", "_")
        conf[opt] = val

    if not args:
        usage()

    if len(args) < 1:
        usage("bad number of arguments")

    buildroot = args[0]
    try:
        outputdir = args[1]
    except IndexError:
        outputdir = "../"

    try:
        deckdebuild.deckdebuild(os.getcwd(), buildroot, outputdir, **conf)
    except deckdebuild.Error, e:
        fatal(e)

if __name__=="__main__":
    main()

