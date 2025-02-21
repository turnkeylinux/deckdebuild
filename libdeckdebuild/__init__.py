# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of DeckDebuild
#
# DeckDebuild is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

from os.path import join, isdir, exists, dirname, lexists, relpath

import os
import sys
import shutil
import subprocess
from subprocess import PIPE
from io import StringIO
import shlex

from libdeckdebuild import debsource
from libdeckdebuild.proctee import proctee_joined, proctee


class DeckDebuildError(Exception):
    pass


def symlink(src, dst):
    if not exists(dirname(dst)):
        os.makedirs(dirname(dst))

    if lexists(dst):
        os.remove(dst)

    os.symlink(src, dst)
    print(f'# ln -s {shlex.quote(src)} {shlex.quote(dst)}')


def system(cmd: list[str], prefix=None):
    proctee_joined(cmd, None, True, prefix=prefix)


def get_returncode(cmd: list[str], prefix=None) -> int:
    return proctee_joined(cmd, None, False, prefix=prefix)[0]


def get_output(cmd: list[str], prefix=None) -> str:
    return proctee(cmd, None, None, False, prefix=prefix)[1].rstrip()


def get_source_dir(name, version):
    if ':' in version:
        version = version.split(':', 1)[1]
    return name + "-" + version


def get_host_arch():
    host_arch = os.uname().machine.lower()
    if host_arch == "x86_64":
        return "amd64"
    # XXX test this on ARM64 machine but should be one of these
    elif host_arch == "aarch64" or host_arch == "arm64":
        return "arm64"
    else:
        # don't know what it is!?
        raise DeckDebuildError(f"Unexpected/unknown architecture {host_arch}")


def apply_faketime_patch(chroot, user):

    patch_command = ["find", "-name", "configure", "-exec",
                     "sed", "-i", "s/test \"$2\" = conftest.file/true/",
                     "{}", ";"]

    system(["chroot", chroot, "su", user, "-l", "-c", *patch_command])


def deckdebuild(
        path: str,
        buildroot: str,
        output_dir: str,
        preserve_build: bool = False,
        user: str = 'build',
        root_cmd: str = 'fakeroot',
        satisfydepends_cmd: str = '/usr/lib/pbuilder/pbuilder-satisfydepends',
        faketime: bool = False,
        vardir: str = '/var/lib/deckdebuilds',
        build_source: bool = False,
        arch: str = get_host_arch()
        ):

    vardir = os.fspath(vardir)

    path_chroots = join(vardir, 'chroots')
    path_builds = join(vardir, 'builds')
    # XXX the arch should be appended to the buildroot, but not yet sure of
    # the best way to do that?
    if not isdir(buildroot):
        raise DeckDebuildError(f"buildroot `{buildroot}' is not a directory")

    source_name = debsource.get_control_fields(path)['Source']
    source_version = debsource.get_version(path)
    source_dir = get_source_dir(source_name, source_version)

    chroot = join(path_chroots, source_dir)

    orig_uid = os.getuid()
    os.setuid(0)

    # delete deck if it already exists
    if exists(chroot):
        system(["deck", "-D", chroot], prefix='undeck')

    # create new deck from the correct buildroot
    print('creating deck', chroot)
    system(["deck", buildroot, chroot], prefix='deck')

    # satisfy dependencies
    os.environ['LANG'] = ""
    os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
    system([satisfydepends_cmd, "--chroot", chroot], prefix='satisfydepends')

    # create user if it doesn't already exist
    user_exists = get_returncode(
            ["chroot", chroot, "getent", "passwd", user],
            prefix='user-check'
            ) == 0
    if not user_exists:
        system(
            ["chroot", chroot, "useradd", "-m", user],
            prefix='add-user')

    orig_cwd = os.getcwd()
    os.chdir(path)

    user_home: str = get_output(
            ["chroot", chroot, "su", user, "-l", "-c", "pwd"],
            prefix='user-home')

    # transfer package over to chroot
    chr_source_dir = join(chroot, relpath(user_home, '/'), source_dir)
    shutil.copytree(path, chr_source_dir)

    # fix permissions for build
    build_uid, build_gid = get_output(
            ['chroot', chroot, 'su', user, '-l', '-c',
             'cat /etc/passwd | grep build | cut -d":" -f3,4'
             ],
            prefix='get uid'
            ).rstrip().split(':')
    build_uid = int(build_uid)
    build_gid = int(build_gid)

    for root, dirs, files in os.walk(chr_source_dir):
        for fn in dirs:
            os.chown(join(root, fn), build_uid, build_gid)
        for fn in files:
            os.chown(join(root, fn), build_uid, build_gid)
    os.chown(chr_source_dir, build_uid, build_gid)
    os.chdir(orig_cwd)

    if faketime:
        apply_faketime_patch(chroot, user)

    # create link to build directory in chroot
    build_dir = chroot + user_home
    build_link = join(path_builds, source_dir)
    symlink(build_dir, build_link)

    # build package in chroot
    build_cmd = f"cd {shlex.quote(source_dir)};"

    if faketime:
        faketime_fmt = debsource.get_mtime(path).strftime("%Y-%m-%d %H:%M:%S")
        build_cmd += f"faketime -f {shlex.quote(faketime_fmt)};"

    build_cmd += "dpkg-buildpackage -d -uc -us"

    if build_source:
        build_cmd += f" -F -r{shlex.quote(root_cmdv)};"
    else:
        build_cmd += f" -b -r{shlex.quote(root_cmd)};"

    trapped = StringIO()
    try:
        proctee_joined(
                ["chroot", chroot, "mount", "-t", "tmpfs", "none", "/dev/shm"],
                output=trapped, check=True, prefix='mount')
        proctee_joined(
                ["chroot",  chroot, "su", user, "-l", "-c", build_cmd],
                output=trapped, check=True, prefix='dpkg-buildpackage')
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        system(["umount", "-f", join(chroot, "dev/shm")])

    os.seteuid(orig_uid)
    output = trapped.getvalue()
    build_log = f"{output_dir}/{source_name}_{source_version}.build"

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
                not fname.endswith('.tar.bz2'):
            continue

        if fname.split("_")[0] in packages:
            src = join(build_dir, fname)
            dst = join(output_dir, fname)

            print(f'# cp {shlex.quote(src)} {shlex.quote(dst)}')
            shutil.copyfile(src, dst)

    if not preserve_build:
        os.seteuid(0)
        system(["deck", "-D", chroot], prefix='undeck')
        os.remove(build_link)

    os.setreuid(orig_uid, 0)
