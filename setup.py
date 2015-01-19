#!/usr/bin/env python

from setuptools import setup
from setuptools import find_packages

setup(
    name='xivo_agid',
    version='1.0',
    description='XIVO AGI Daemon',
    author='Avencall',
    author_email='technique@proformatique.com',
    url='http://xivo.io/',
    packages=find_packages(),
    data_files=[
        ('/usr/sbin', ['sbin/xivo-agid'])
    ]
)
