# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of DeckDebuild
#
# DeckDebuild is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import re
from datetime import datetime
from email.utils import parsedate
from os.path import exists, join

from debian import deb822


class DebSourceError(Exception):
    pass


def get_control_fields(path: str) -> dict[str, str]:
    controlfile = join(path, "debian/control")
    control_dict: dict[str, str] = dict()
    for paragraph in deb822.Deb822.iter_paragraphs(open(controlfile)):
        control_dict.update(paragraph)
    return control_dict


def get_packages(path: str) -> list[str]:
    controlfile = join(path, "debian/control")
    return [
        re.sub(r"^.*?:", "", line).strip()
        for line in open(controlfile).readlines()
        if re.match(r"^Package:", line, re.I)
    ]


def get_version(path: str) -> str:
    changelogfile = join(path, "debian/changelog")

    if not exists(changelogfile):
        raise DebSourceError(f"no such file or directory `{changelogfile}'")

    for line in open(changelogfile).readlines():
        m = re.match(
            r"^\w[-+0-9a-z.]* \(([^\(\) \t]+)\)(?:\s+[-+0-9a-z.]+)+\;",
            line,
            re.I,
        )
        if m:
            return m.group(1)
    raise DebSourceError(f"can't parse version from `{changelogfile}'")


def get_mtime(path: str) -> datetime:

    changelogfile = join(path, "debian/changelog")

    for line in open(changelogfile).readlines():
        if not line.startswith(" -- "):
            continue
        break

    m = re.match(".*>  (.*)", line)
    assert m
    parsed_date = parsedate(m.group(1))
    if parsed_date is not None:
        return datetime(*parsed_date[:6])
    raise DebSourceError(f"Parsing date failed: {m.group(1)}")
