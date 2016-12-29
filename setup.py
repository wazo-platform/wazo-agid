#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages


setup(
    name='xivo_agid',
    version='1.1',
    description='XIVO AGI Daemon',
    author='Wazo Authors',
    author_email='dev.wazo@gmail.com',
    url='http://wazo.community',
    license='GPLv3',
    packages=find_packages(),
    scripts=['bin/xivo-agid']
)
