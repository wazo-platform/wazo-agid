# -*- coding: utf-8 -*-

# Copyright (C) 2012-2014 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import argparse

from xivo_agid import agid
from xivo_agid.modules import *
from xivo import daemonize
from xivo.xivo_logging import setup_logging

PIDFILE = '/var/run/xivo-agid.pid'
LOG_FILE_NAME = '/var/log/xivo-agid.log'


def main():
    parsed_args = _parse_args()

    setup_logging(LOG_FILE_NAME, parsed_args.foreground, parsed_args.debug)

    if not parsed_args.foreground:
        daemonize.daemonize()

    daemonize.lock_pidfile_or_die(PIDFILE)
    try:
        agid.init()
        agid.run()
    finally:
        daemonize.unlock_pidfile(PIDFILE)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', action='store_true', dest='foreground',
                        help='run in foreground')
    parser.add_argument('-d', action='store_true', dest='debug',
                        help='increase verbosity')

    return parser.parse_args()


if __name__ == '__main__':
    main()
