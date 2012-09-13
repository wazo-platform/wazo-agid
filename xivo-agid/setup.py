#!/usr/bin/env python

__version__ = "$Revision$ $Date$"

from distutils.core import setup

setup(name='xivo_agid',
      version='1.0',
      description='XIVO AGI Daemon',
      author='Proformatique',
      author_email='technique@proformatique.com',
      url='http://xivo.fr/',
      packages=['xivo_agid',
                'xivo_agid.modules',
                'xivo_agid.directory',
                'xivo_agid.directory.data_sources',
                'xivo_agid.handlers'],
      data_files=[
                  ('/usr/sbin', ['sbin/agid']),
                 ],
     )
