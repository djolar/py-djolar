#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys

from setuptools import setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_long_description():
    """
    Return the README.
    """
    return open('README.md', 'r', encoding="utf8").read()


setup(
    name='djolar',
    version=get_version('djolar'),
    url='https://github.com/enix223/djolar',
    license='MIT',
    description='A simple and light weight model search module for django, easy to connect front-end with backend.',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='Enix Yu',
    author_email='enixyu@cloudesk.top',
    packages=('djolar', ),
    install_requires=[
        "django>=1.11",
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
