#!/usr/bin/env python3

from distutils.core import setup

setup(
    name="deckdebuild",
    version="2.0.0alpha",
    author="Jeremy Davis",
    author_email="jeremy@turnkeylinux.org",
    url="https://github.com/turnkeylinux/deckdebuild",
    packages=["libdeckdebuild"],
    scripts=["deckdebuild"]
)
