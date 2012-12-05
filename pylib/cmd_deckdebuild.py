#!/usr/bin/python
# Copyright (c) TurnKey Linux - http://www.turnkeylinux.org
#
# This file is part of DeckDebuild
#
# DeckDebuild is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""Syntax: $AV0 [-options] /path/to/buildroot [ /path/to/output-dir ]
build a Debian package in a decked chroot

Output dir defaults to ../
"""

import os
import re
import sys
import help
import deckdebuild

import cliconf
from cliconf import Opt, BoolOpt

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

class Opts(cliconf.Opts):
    faketime = BoolOpt("use faketime (must be installed in buildroot)",
                       default=False)

    preserve_build = BoolOpt("don't remove build deck after build",
                             short="p", default=False)

    user = Opt("build username (created if it doesn't exist)",
               short="u", default="build")

    root_cmd = Opt("command userd to gain root_privileges",
                   short="r", default="fakeroot")

    satisfydepends_cmd = Opt("program used to satisfy build dependencies", 
                             protect=True,
                             default="/usr/lib/pbuilder/pbuilder-satisfydepends")

    vardir = Opt("var data path", protect=True, default="/var/lib/deckdebuild")

class CliConf(cliconf.CliConf):
    __doc__ = __doc__

    Opts = Opts

    env_path = "DECKDEBUILD_"
    file_path = "/etc/deckdebuild.conf"

usage = CliConf.usage

def main():
    try:
        opts, args = CliConf.getopt()
    except CliConf.Error, e:
        CliConf.usage(e)

    if not args:
        CliConf.usage()

    if len(args) < 1:
        CliConf.usage("bad number of arguments")

    buildroot = args[0]
    try:
        outputdir = args[1]
    except IndexError:
        outputdir = "../"

    conf = dict([ (opt.name, opt.val) for opt in opts ])
    try:
        deckdebuild.deckdebuild(os.getcwd(), buildroot, outputdir, **conf)
    except deckdebuild.Error, e:
        fatal(e)

if __name__=="__main__":
    main()

