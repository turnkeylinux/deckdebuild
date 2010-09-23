from os.path import *

import os
import re
import shutil
import commands

import stdtrap
from paths import Paths

class Error(Exception):
    pass

def symlink(src, dst):
    if not exists(dirname(dst)):
        os.makedirs(dirname(dst))
        
    if lexists(dst):
        os.remove(dst)

    os.symlink(src, dst)

def mkargs(*args):
    return tuple(map(commands.mkarg, args))

def system(command, *args):
    command = command + " " + " ".join(mkargs(*args))
    print "# " + command
    
    err = os.system(command)
    if err:
        raise Error("command failed: " + command,
                    os.WEXITSTATUS(err))

def getoutput(command):
    (s,o) = commands.getstatusoutput(command)
    return o

class _DeckDebuildPaths(Paths):
    def __init__(self, path="/var/lib/deckdebuild"):
        Paths.__init__(self, path,
                       ['chroots',
                        'builds'])

paths = _DeckDebuildPaths()

def get_control_packages(controlfile="debian/control"):
    return [ re.sub(r'^.*?:', '', line).strip()
             for line in file(controlfile).readlines()
             if re.match(r'^Package:', line, re.I) ]

def deckdebuild(path, buildroot, output_dir,
                preserve_build=False, user='build', root_cmd='fakeroot',
                satisfydepends_cmd='/usr/lib/pbuilder/pbuilder-satisfydepends'):

    if not isdir(buildroot):
        raise Error("buildroot `%s' is not a directory" % buildroot)

    orig_cwd = os.getcwd()
    os.chdir(path)

    package_dir = basename(realpath(path))
    chroot = join(paths.chroots, package_dir)

    orig_uid = os.getuid()
    os.setuid(0)
    
    # delete deck if it already exists
    if exists(chroot):
        system("deck -D", chroot)

    # create new deck from the correct buildroot
    system("deck", buildroot, chroot)

    # satisfy dependencies
    os.environ['LANG'] = ""
    os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
    system(satisfydepends_cmd, "--chroot", chroot)

    # create user if it doesn't already exist
    userent = getoutput("chroot %s getent passwd %s" % mkargs(chroot, user))
    if not userent:
        system("chroot", chroot, "useradd", "-m", user)

    # transfer package over to chroot
    system("tar -C ../ -cf - %s | chroot %s su %s -l -c 'tar -xf -'" % 
           mkargs(package_dir, chroot, user))

    # create link to build directory in chroot
    user_home = getoutput("chroot %s su %s -l -c 'pwd'" % mkargs(chroot, user))
    
    build_dir = chroot + user_home
    build_link = join(paths.builds, package_dir)
    symlink(build_dir, build_link)
    
    # build package in chroot
    build_cmd = "cd %s; dpkg-buildpackage -uc -us -b -r%s" % \
                (package_dir, root_cmd)
    
    trap = stdtrap.UnitedStdTrap(transparent=True)
    try:
        system("chroot %s su %s -l -c %s" % mkargs(chroot, user, build_cmd))
    finally:
        trap.close()

    os.seteuid(orig_uid)
    output = trap.std.read()
    file("%s/%s.build" % (output_dir, package_dir), "w").write(output)

    # copy packages
    packages = get_control_packages()

    for fname in os.listdir(build_dir):
        if not fname.endswith(".deb"):
            continue

        if fname.split("_")[0] in packages:
            src = join(build_dir, fname)
            dst = join(output_dir, fname)
            
            shutil.copyfile(src, dst)

    if not preserve_build:
        os.seteuid(0)
        system("deck -D", chroot)
        os.remove(build_link)

    os.chdir(orig_cwd)
    os.setreuid(orig_uid, 0)
