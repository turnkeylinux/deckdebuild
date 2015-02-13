A pbuilder replacement which leverages deck
===========================================

builds a Debian package in a decked chroot

Usage example::

	cd /path/to/package

	deckdebuild /path/to/buildroot

		*.debs and *.build log in ../

Note, you don't have to be root for this to work as deckdebuild is
installed a suid root program. With grsecurity chroot hardening, using
chroot is safe, even in suid mode. Otherwise, not so much.

Features
--------

- builds packages inside self contained buildroots

- supports using deck (a high level aufs interface) to create a
  throwaway copy-on-write fork of the buildroot

- supports deterministic builds using faketime to control timestamps

How it works
------------

1) decks the buildroot to /var/lib/deckdebuild/chroots/<package>
2) satisfies build dependencies in the decked buildroot
3) copies over the package under the specified user into the new buildroot
4) builds the package while intercepting the output
5) copies packages output of the decked buildroot to output-dir (e.g., ../)
6) destroys the buildroot (unless --preserve-build)

Notes on deterministic package builds using faketime
----------------------------------------------------

It is usually impossible for two Debian developers to produce a Debian
package with the same sha1sum signature because the temporary
directories and files created during the build process will have
different timestamps.

Even if you go as far as set the time on the machine that will still not
be enough because there is no guarantee that the build will exactly the
same amount of time on two different machines or even when executed
twice on the same machine.

While mulling over the problem I realized this it should be possible to
use LD_PRELOAD trick to intercept the various libc called involved and
make them return a fake "frozen" timestamp.

I googled first a bit and just our luck it turns out such a program has
already been written - faketime.

How deckdebuild uses faketime
'''''''''''''''''''''''''''''

Faketime is installed in the buildroot. When --faketime is specified,
deckdebuild will invoke faketime as a wrapper to dpkg-buildpackage.

We use faketime to "freeze" the time to the time of the last entry in the
changelog.

We then patch the pool to invoke deckdebuild with --faketime.

Usage
-----

::

    Syntax: deckdebuild [-options] /path/to/buildroot [ /path/to/output-dir ]
    build a Debian package in a decked chroot

    Output dir defaults to ../

    Resolution order for options:
    1) command line (highest precedence)
    2) environment variable
    3) configuration file (/etc/deckdebuild.conf)
    4) built-in default (lowest precedence)

    Options:
      -r --root-cmd=         command userd to gain root_privileges
                             environment: DECKDEBUILD_ROOT_CMD
                             default: fakeroot

      -u --user=             build username (created if it doesn't exist)
                             environment: DECKDEBUILD_USER
                             default: build

      -p --preserve-build    don't remove build deck after build
                             environment: DECKDEBUILD_PRESERVE_BUILD
                             default: False


    Protected options (root only):

      --satisfydepends-cmd=  program used to satisfy build dependencies
                             environment: DECKDEBUILD_SATISFYDEPENDS_CMD
                             default: /usr/lib/pbuilder/pbuilder-satisfydepends

      --vardir=              var data path
                             environment: DECKDEBUILD_VARDIR
                             default: /var/lib/deckdebuild

    Configuration file format (/etc/deckdebuild.conf):

      <option-name> <value>

Installation
============

* Dependencies: pbuilder, deck

Design
======

Filesystem structure::

    /var/lib/deckdebuild

        chroots/<package>
            /home/<user>/<package>

        builds/<package> -> ../chroots/<package>/home/<user>/<package>

Psuedo-logic::

    data flow
        input: package source directory
        output: 
            binary debs
            <package-source-name>.build

    export DEBIAN_FRONTEND="noninteractive"
    
    parse options
        option precedence
            cli option
            environment
            built-in default       

    check that we are running as root (we need root privileges)

    deck the build root

    install the build dependencies
        /usr/lib/pbuilder/pbuilder-satisfydepends --chroot /path/to/build/root
            installs build-dependencies
                doesn't check if they already exist

    if build user doesn't exist create a build user
    copy the package over to the build user's home
    build the package with dpkg-buildpackage under fakeroot
        fakeroot dpkg-buildpackage -rfakeroot -uc -us -b

    if the build fails, raise an exception?

    if the build succeeds put the packages in the parent directory of the source package + build log

    unless -p, we delete the deck environment the package was built in
