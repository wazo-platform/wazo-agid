# -*- coding: utf-8 -*-

# Copyright (C) 2012-2015 Avencall
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

from xivo.chain_map import ChainMap
from xivo.config_helper import read_config_file_hierarchy

from xivo_agid import agid
from xivo_agid.modules import *
from xivo.daemonize import pidfile_context
from xivo.xivo_logging import setup_logging

_DEFAULT_CONFIG = {
    'debug': False,
    'foreground': False,
    'pidfile': '/var/run/xivo-agid.pid',
    'logfile': '/var/log/xivo-agid.log',
    'listen_port': 4573,
    'listen_address': '127.0.0.1',
    'config_file': '/etc/xivo-agid/config.yml',
    'extra_config_files': '/etc/xivo-agid/conf.d/',
    'connection_pool_size': 10,
    'db_uri': 'postgresql://asterisk:proformatique@localhost/asterisk?charset=utf8',
}


def main():
    cli_config = _parse_args()
    file_config = read_config_file_hierarchy(ChainMap(cli_config, _DEFAULT_CONFIG))
    config = ChainMap(cli_config, file_config, _DEFAULT_CONFIG)

    setup_logging(config['logfile'], config['foreground'], config['debug'])

    with pidfile_context(config['pidfile'], config['foreground']):
        agid.init(config)
        agid.run()


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', action='store_true', dest='foreground',
                        help='run in foreground')
    parser.add_argument('-d', action='store_true', dest='debug',
                        help='increase verbosity')

    parsed_args = parser.parse_args()

    config = {}
    if parsed_args.debug:
        config['debug'] = parsed_args.debug
    if parsed_args.foreground:
        config['foreground'] = parsed_args.foreground

    return config


if __name__ == '__main__':
    main()
