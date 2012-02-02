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
