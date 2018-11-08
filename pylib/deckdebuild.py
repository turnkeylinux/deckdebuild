# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of DeckDebuild
#
# DeckDebuild is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

from os.path import *

import os
import shutil
import commands

import stdtrap
from paths import Paths

import debsource

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

class DeckDebuildPaths(Paths):
    files = ['chroots', 'builds']

def get_source_dir(name, version):
    if ':' in version:
        version = version.split(':', 1)[1]
    return name + "-" + version

def apply_faketime_patch(chroot, user):

    patch_command = "find -name configure -exec sed -i 's/test \"$2\" = conftest.file/true/' {} \;"

    system("chroot %s su %s -l -c %s" % \
           mkargs(chroot, user, patch_command))

def deckdebuild(path, buildroot, output_dir,
                preserve_build=False, user='build', root_cmd='fakeroot',
                satisfydepends_cmd='/usr/lib/pbuilder/pbuilder-satisfydepends',
                faketime=False,
                vardir='/var/lib/deckdebuild',
                build_source=False):

    paths = DeckDebuildPaths(vardir)

    if not isdir(buildroot):
        raise Error("buildroot `%s' is not a directory" % buildroot)

    source_name = debsource.get_control_fields(path)['Source']
    source_version = debsource.get_version(path)

    source_dir = get_source_dir(source_name, source_version)

    chroot = join(paths.chroots, source_dir)

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

    orig_cwd = os.getcwd()
    os.chdir(path)
    # transfer package over to chroot
    system("tar -cf - . | chroot %s su %s -l -c \"mkdir -p %s && tar -C %s -xf -\"" %
           mkargs(chroot, user, source_dir, source_dir))
    os.chdir(orig_cwd)

    if faketime:
        apply_faketime_patch(chroot, user)

    # create link to build directory in chroot
    user_home = getoutput("chroot %s su %s -l -c 'pwd'" % mkargs(chroot, user))

    build_dir = chroot + user_home
    build_link = join(paths.builds, source_dir)
    symlink(build_dir, build_link)

    # build package in chroot
    build_cmd = "cd %s; " % source_dir

    if faketime:
        faketime_fmt = debsource.get_mtime(path).strftime("%Y-%m-%d %H:%M:%S")
        build_cmd += "faketime -f '%s' " % faketime_fmt

    if build_source:
        build_cmd += "dpkg-buildpackage -d -uc -us -F -r%s" % root_cmd
    else:
        build_cmd += "dpkg-buildpackage -d -uc -us -b -r%s" % root_cmd

    trap = stdtrap.UnitedStdTrap(transparent=True)
    try:
        system("chroot %s mount -t tmpfs none /dev/shm" % mkargs(chroot))
        system("chroot %s su %s -l -c %s" % mkargs(chroot, user, build_cmd))
    finally:
        system("umount -f %s/dev/shm" % mkargs(chroot))
        trap.close()

    os.seteuid(orig_uid)
    output = trap.std.read()
    build_log = "%s/%s_%s.build" % (output_dir, source_name, source_version)

    with open(build_log, 'w') as fob:
        fob.write(output)

    # copy packages
    packages = debsource.get_packages(path)

    for fname in os.listdir(build_dir):
        if not fname.endswith(".deb") and\
                not fname.endswith(".udeb") and\
                not fname.endswith('.buildinfo') and\
                not fname.endswith('.tar.xz') and\
                not fname.endswith('.tar.gz') and\
                not fname.endswith('.tar.bz2') and\:
            continue

        if fname.split("_")[0] in packages:
            src = join(build_dir, fname)
            dst = join(output_dir, fname)

            shutil.copyfile(src, dst)

    if not preserve_build:
        os.seteuid(0)
        system("deck -D", chroot)
        os.remove(build_link)

    os.setreuid(orig_uid, 0)
