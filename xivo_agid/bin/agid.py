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
import logging
import xivo_dao

from xivo.chain_map import ChainMap
from xivo.config_helper import read_config_file_hierarchy
from xivo.config_helper import parse_config_file

from xivo_agid import agid
from xivo_agid.modules import *
from xivo.daemonize import pidfile_context
from xivo.xivo_logging import setup_logging, silence_loggers

_DEFAULT_CONFIG = {
    'dird': {
        'host': 'localhost',
        'port': 9489,
        'timeout': 1,
        },
    'auth': {
        'host': 'localhost',
        'port': 9497,
        'key_file': '/var/lib/xivo-auth-keys/xivo-agid-key.yml'
        },
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
    key_config = _load_key_file(ChainMap(cli_config, file_config, _DEFAULT_CONFIG))
    config = ChainMap(cli_config, key_config, file_config, _DEFAULT_CONFIG)

    setup_logging(config['logfile'], config['foreground'], config['debug'])
    silence_loggers(['urllib3'], logging.WARNING)

    xivo_dao.init_db_from_config(config)

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


def _load_key_file(config):
    key_file = parse_config_file(config['auth'].get('key_file', ''))
    return {'auth': {'service_id': key_file['service_id'],
                     'service_key': key_file['service_key']}}


if __name__ == '__main__':
    main()
