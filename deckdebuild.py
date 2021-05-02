#!/usr/bin/python3
# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of DeckDebuild
#
# DeckDebuild is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import argparse
import os
import sys
from os import environ

from libdeckdebuild import deckdebuild, DeckDebuildError
from conffile import ConfFile

default_values = {
    "root_cmd": "fakeroot",
    "user": "build",
    "preserve_build": False,
    "faketime": False,
    "satisfydepends_cmd": "/usr/lib/pbuilder/pbuilder-satisfydepends",
    "vardir": "/var/lib/deckdebuild",
    "build_source": False,
    "path_to_buildroot": "",
    "path_to_output_dir": os.getcwd()
    }


def fatal(s):
    print("error: " + str(s), file=sys.stderr)
    sys.exit(1)


class Config(ConfFile):
    CONF_FILE = "/etc/deckdebuild.conf"


def get_env(prefix="DECKDEBUILD_"):
    items = {}
    for key in environ.keys():
        if key.startswith(prefix):
            name = key[len(prefix):].lower()
            self.items[name] = environ[key]
    return items


class Conf(dict):
    def __init__(self, conf_file=Config(), prefix="DECKDEBUILD_"):
        env = get_env(prefix=prefix)
        conf_file = Config()
        default = {}
        for key, value in default_values.items():
            if key in conf_file:
                value = conf_file[key]
            if key in env:
                value = env[key]
            if isinstance(value,  bool):
                action = "store_{}".format(str(not value).lower())
                new_key = key+'_action'
                default[new_key] = action
            default[key] = value
        super(Conf, self).__init__(**default)
        self.__dict__ = self


def main():
    conf = Conf()

    parser = argparse.ArgumentParser(
             description="build a Debian package in a decked chroot")
    parser.add_argument("-r", "--root-cmd",
                        help="command used to gain root_privileges"
                             " env: DECKDEBUILD_ROOT_CMD"
                             " default: {}".format(conf.root_cmd),
                        default=conf.root_cmd)
    parser.add_argument("-u", "--user",
                        help="build username (created if it doesn't exist)"
                             " env: DECKDEBUILD_USER"
                             " default: {}".format(conf.user),
                        default=conf.user)
    parser.add_argument("-p", "--preserve-build",
                        help="don't remove build deck after build"
                             " env: DECKDEBUILD_PRESERVE_BUILD"
                             " default: {}".format(conf.preserve_build),
                        action=conf.preserve_build_action)
    parser.add_argument("-f", "--faketime",
                        help="use faketime (must be installed)"
                             " env: DECKDEBUILD_FAKETIME"
                             " default: {}".format(conf.faketime),
                        action=conf.faketime_action)
    parser.add_argument("--satisfydepends-cmd",
                        help="program used to satisfy build dependencies"
                             " env: DECKDEBUILD_SATISFYDEPENDS_CMD"
                             " default: {}".format(conf.satisfydepends_cmd),
                        default=conf.satisfydepends_cmd)
    parser.add_argument("--vardir",
                        help="var data path"
                             " env: DECKDEBUILD_VARDIR"
                             " default: {}".format(conf.vardir),
                        default=conf.vardir)
    parser.add_argument("-b", "--build-source",
                        help="Build source package too."
                             " env: DECKDEBUILD_BUILD_SOURCE"
                             " default: {}".format(conf.build_source),
                        action=conf.build_source_action)
    parser.add_argument("path_to_buildroot",
                        help="Path to an exisiting buildroot")
    parser.add_argument("path_to_output_dir", nargs='?',
                        help="Path to output",
                        default=os.getcwd())
    args = parser.parse_args()
    try:
        deckdebuild(os.getcwd(),
                    args.path_to_buildroot, args.path_to_outputdir,
                    root_cmd=args.root_cmd, user=args.user,
                    preserve_build=args.preserve_build,
                    faketime=args.faketime,
                    satisfydepends_cmd=args.satisfydepends_cmd,
                    vardir=args.vardir,
                    build_source=args.build_source)
    except DeckDebuildError as e:
        fatal(e)


if __name__=='__main__':
    main()
