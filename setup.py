#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code is distributed under the GPLv3 license.
# Copyright (c) Polytechnique.org


import codecs
import os
import re

from setuptools import find_packages, setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    init_path = os.path.join(root_dir, *(package_components + ['__init__.py']))
    with codecs.open(init_path, 'r', 'utf-8') as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.1.1'

PACKAGE = 'xorgdata'

setup(
    name=PACKAGE,
    version=get_version(PACKAGE),
    author="Polytechnique.org dev team",
    author_email="devel+xorgdata@staff.polytechnique.org",
    description="Polytechnique.org central datastore",
    license='AGPLv3',
    url='https://github.com/Polytechnique-org/%s' % PACKAGE,

    packages=find_packages(include=[PACKAGE, '%s.*' % PACKAGE]),
    include_package_data=True,

    python_requires='>=3.4.2',
    install_requires=[
        'Django>=2.0,<2.3',
        'getconf',
    ],
    setup_requires=[
        'setuptools>=0.8',
    ],

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Natural Language :: French',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP :: Session',
        'Topic :: System :: Systems Administration :: Authentication/Directory'
    ],
)
