#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages


setup(
    name='xivo_agid',
    version='1.1',
    description='XIVO AGI Daemon',
    author='Proformatique Inc.',
    author_email='dev+pkg@proformatique.com',
    url='http://xivo.io/',
    license='GPLv3',
    packages=find_packages(),
    scripts=['bin/xivo-agid']
)
