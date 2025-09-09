# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of DeckDebuild
#
# DeckDebuild is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import re
from debian import deb822
from os.path import *


class Error(Exception):
    pass


def get_control_fields(path):
    controlfile = join(path, "debian/control")
    control_dict = dict()
    for paragraph in deb822.Deb822.iter_paragraphs(open(controlfile)):
        control_dict.update(paragraph)
    return control_dict


def get_packages(path):
    controlfile = join(path, "debian/control")
    return [
        re.sub(r"^.*?:", "", line).strip()
        for line in open(controlfile).readlines()
        if re.match(r"^Package:", line, re.I)
    ]


def get_version(path):
    changelogfile = join(path, "debian/changelog")

    if not exists(changelogfile):
        raise Error("no such file or directory `%s'" % changelogfile)

    for line in open(changelogfile).readlines():
        m = re.match(
            "^\w[-+0-9a-z.]* \(([^\(\) \t]+)\)(?:\s+[-+0-9a-z.]+)+\;",
            line,
            re.I,
        )
        if m:
            return m.group(1)
    raise Error("can't parse version from `%s'" % changelogfile)


def get_mtime(path):
    from email.utils import parsedate
    import datetime

    changelogfile = join(path, "debian/changelog")

    for line in open(changelogfile).readlines():
        if not line.startswith(" -- "):
            continue
        break

    m = re.match(".*>  (.*)", line)
    assert m

    return datetime.datetime(*parsedate(m.group(1))[:6])
