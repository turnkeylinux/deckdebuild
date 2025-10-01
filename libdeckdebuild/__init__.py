# Copyright (c) TurnKey GNU/Linux - https//www.turnkeylinux.org
#
# This file is part of DeckDebuild
#
# DeckDebuild is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import os
import shlex
import shutil
import sys
from io import StringIO
from os.path import dirname, exists, isdir, join, lexists, relpath

from libdeckdebuild import debsource
from libdeckdebuild.proctee import proctee, proctee_joined


class DeckDebuildError(Exception):
    pass


def symlink(src: str, dst: str) -> None:
    if not exists(dirname(dst)):
        os.makedirs(dirname(dst))

    if lexists(dst):
        os.remove(dst)

    os.symlink(src, dst)
    print(f"# ln -s {shlex.quote(src)} {shlex.quote(dst)}")


def system(cmd: list[str], prefix: str | None = None) -> None:
    proctee_joined(cmd, None, True, prefix=prefix)


def get_returncode(cmd: list[str], prefix: str | None = None) -> int:
    return proctee_joined(cmd, None, False, prefix=prefix)[0]


def get_output(cmd: list[str], prefix: str | None = None) -> str:
    return proctee(cmd, None, None, False, prefix=prefix)[1].rstrip()


def get_source_dir(name: str, version: str) -> str:
    if ":" in version:
        version = version.split(":", 1)[1]
    return name + "-" + version


def deckdebuild(
    path: str,
    buildroot: str,
    output_dir: str,
    preserve_build: str = "error",
    user: str = "build",
    root_cmd: str = "fakeroot",
    satisfydepends_cmd: str = "/usr/lib/pbuilder/pbuilder-satisfydepends",
    faketime: bool = True,
    vardir: str = "/var/lib/deckdebuilds",
    build_source: bool = False,
) -> None:
    vardir = os.fspath(vardir)

    path_chroots = join(vardir, "chroots")
    path_builds = join(vardir, "builds")

    if not isdir(buildroot):
        raise DeckDebuildError(
            f"buildroot chroot `{buildroot}' is not a directory"
        )

    source_name = debsource.get_control_fields(path)["Source"]
    source_version = debsource.get_version(path)
    source_dir = get_source_dir(source_name, source_version)

    chroot = join(path_chroots, source_dir)

    orig_uid = os.getuid()
    os.setuid(0)

    # delete deck if it already exists
    if exists(chroot):
        print(
            f"warning: build chroot deck '{chroot}' exists; removing",
            file=sys.stderr,
        )
        system(["deck", "-D", chroot], prefix="undeck")

    # create new deck from the correct buildroot
    print(f"creating build chroot deck: {chroot}")
    system(["deck", buildroot, chroot], prefix="deck")

    # satisfy dependencies
    os.environ["LANG"] = ""
    os.environ["DEBIAN_FRONTEND"] = "noninteractive"
    system([satisfydepends_cmd, "--chroot", chroot], prefix="satisfydepends")

    # create user if it doesn't already exist
    user_exists = (
        get_returncode(
            ["chroot", chroot, "getent", "passwd", user], prefix="user-check"
        )
        == 0
    )
    if not user_exists:
        system(["chroot", chroot, "useradd", "-m", user], prefix="add-user")

    orig_cwd = os.getcwd()
    os.chdir(path)

    user_home: str = get_output(
        ["chroot", chroot, "su", user, "-l", "-c", "pwd"], prefix="user-home"
    )

    # transfer package over to chroot
    chr_source_dir = join(chroot, relpath(user_home, "/"), source_dir)
    shutil.copytree(path, chr_source_dir)

    # fix permissions for build
    build_uid, build_gid = (
        get_output(
            [
                "chroot",
                chroot,
                "su",
                user,
                "-l",
                "-c",
                "grep '^build:' /etc/passwd | cut -d':' -f3,4",
            ],
            prefix="get uid",
        )
        .rstrip()
        .split(":")
    )
    build_uid_int = int(build_uid)
    build_gid_int = int(build_gid)

    for root, dirs, files in os.walk(chr_source_dir):
        for fn in dirs:
            os.chown(join(root, fn), build_uid_int, build_gid_int)
        for fn in files:
            os.chown(join(root, fn), build_uid_int, build_gid_int)
    os.chown(chr_source_dir, build_uid_int, build_gid_int)
    os.chdir(orig_cwd)

    # create link to build directory in chroot
    build_dir = chroot + user_home
    build_link = join(path_builds, source_dir)
    symlink(build_dir, build_link)

    # build package in chroot
    build_cmd = f"cd {shlex.quote(source_dir)};"

    if faketime:
        faketime_fmt = debsource.get_mtime(path).strftime("%Y-%m-%d %H:%M:%S")
        build_cmd += f"faketime -f {shlex.quote(faketime_fmt)};"

    if build_source:
        build_cmd += (
            f"dpkg-buildpackage -d -uc -us -F -r{shlex.quote(root_cmd)}"
        )
    else:
        build_cmd += (
            f"dpkg-buildpackage -d -uc -us -b -r{shlex.quote(root_cmd)}"
        )

    trapped = StringIO()
    error = False
    try:
        proctee_joined(
            ["chroot", chroot, "mount", "-t", "tmpfs", "none", "/dev/shm"],
            output=trapped,
            check=True,
            prefix="mount",
        )
        proctee_joined(
            ["chroot", chroot, "su", user, "-l", "-c", build_cmd],
            output=trapped,
            check=True,
            prefix="dpkg-buildpackage",
        )
    except Exception:
        import traceback

        traceback.print_exc()
        error = True
    finally:
        system(["umount", "-f", join(chroot, "dev/shm")])

    os.seteuid(orig_uid)
    output = trapped.getvalue()
    build_log = f"{output_dir}/{source_name}_{source_version}.build"

    with open(build_log, "w") as fob:
        fob.write(output)

    # copy packages
    packages = debsource.get_packages(path)

    for fname in os.listdir(build_dir):
        if (
            not fname.endswith(".deb")
            and not fname.endswith(".udeb")
            and not fname.endswith(".buildinfo")
            and not fname.endswith(".tar.xz")
            and not fname.endswith(".tar.gz")
            and not fname.endswith(".tar.bz2")
        ):
            error = True
            continue

        if fname.split("_")[0] in packages:
            src = join(build_dir, fname)
            dst = join(output_dir, fname)

            print(f"# cp {shlex.quote(src)} {shlex.quote(dst)}")
            shutil.copyfile(src, dst)

    if error:
        print(
            f"building {source_name}_{source_version} package failed"
            f"\n - see build log ({build_log}) &/or previous output for info",
            file=sys.stderr,
        )
    else:
        print(f"built {source_name}_{source_version} successfully")
    preserve_reason = f"(preserve-build = {preserve_build}; error = {error})"
    if preserve_build == "never" or (
        not error and preserve_build == "on-error"
    ):
        print(f"deleting {chroot} {preserve_reason}")
        os.seteuid(0)
        system(["deck", "-D", chroot], prefix="undeck")
        os.remove(build_link)
    else:
        print(f"retaining {chroot} {preserve_reason}")

    os.setreuid(orig_uid, 0)
