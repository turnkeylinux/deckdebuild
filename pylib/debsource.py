# Copyright (c) TurnKey Linux - http://www.turnkeylinux.org
#
# This file is part of DeckDebuild
#
# DeckDebuild is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import re
from os.path import *

class Error(Exception):
    pass

def get_control_fields(path):
    controlfile = join(path, "debian/control")
    return dict([ re.split("\s*:\s+", line.strip(), 1)
                  for line in file(controlfile).readlines()
                  if line.strip() and not line.startswith(" ") ])
    
def get_packages(path):
    controlfile = join(path, "debian/control")
    return [ re.sub(r'^.*?:', '', line).strip()
             for line in file(controlfile).readlines()
             if re.match(r'^Package:', line, re.I) ]

def get_version(path):
    changelogfile = join(path, "debian/changelog")
    
    if not exists(changelogfile):
        raise Error("no such file or directory `%s'" % changelogfile)
    
    for line in file(changelogfile).readlines():
        m = re.match('^\w[-+0-9a-z.]* \(([^\(\) \t]+)\)(?:\s+[-+0-9a-z.]+)+\;',line, re.I)
        if m:
            return m.group(1)
    raise Error("can't parse version from `%s'" % changelogfile)

def get_mtime(path):
    import rfc822
    import datetime

    changelogfile = join(path, "debian/changelog")

    for line in file(changelogfile).readlines():
        if not line.startswith(" -- "):
            continue
        break

    m = re.match('.*>  (.*)', line)
    assert m

    return datetime.datetime(*rfc822.parsedate(m.group(1))[:6])
