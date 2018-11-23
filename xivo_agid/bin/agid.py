# -*- coding: utf-8 -*-
# Copyright 2012-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import argparse
import logging
import xivo_dao

from wazo_dird_client import Client as DirdClient
from xivo.chain_map import ChainMap
from xivo.config_helper import parse_config_file
from xivo.config_helper import read_config_file_hierarchy
from xivo.daemonize import pidfile_context
from xivo.token_renewer import TokenRenewer
from xivo.user_rights import change_user
from xivo.xivo_logging import setup_logging, silence_loggers
from xivo_agentd_client import Client as AgentdClient
from xivo_auth_client import Client as AuthClient
from xivo_confd_client import Client as ConfdClient

from xivo_agid import agid
from xivo_agid.modules import *

_DEFAULT_CONFIG = {
    'dird': {
        'host': 'localhost',
        'port': 9489,
        'timeout': 1,
        'verify_certificate': '/usr/share/xivo-certs/server.crt'
    },
    'auth': {
        'host': 'localhost',
        'port': 9497,
        'key_file': '/var/lib/wazo-auth-keys/xivo-agid-key.yml',
        'verify_certificate': '/usr/share/xivo-certs/server.crt'
    },
    'user': 'xivo-agid',
    'debug': False,
    'foreground': False,
    'pidfile': '/var/run/xivo-agid/xivo-agid.pid',
    'logfile': '/var/log/xivo-agid.log',
    'listen_port': 4573,
    'listen_address': '127.0.0.1',
    'config_file': '/etc/xivo-agid/config.yml',
    'extra_config_files': '/etc/xivo-agid/conf.d/',
    'connection_pool_size': 10,
    'db_uri': 'postgresql://asterisk:proformatique@localhost/asterisk?charset=utf8',
    'call_recording': {
        'filename_template': 'user-{{ srcnum }}-{{ dstnum }}-{{ timestamp }}',
        'filename_extension': 'wav',
    },
}


def main():
    cli_config = _parse_args()
    file_config = read_config_file_hierarchy(ChainMap(cli_config, _DEFAULT_CONFIG))
    key_config = _load_key_file(ChainMap(cli_config, file_config, _DEFAULT_CONFIG))
    config = ChainMap(cli_config, key_config, file_config, _DEFAULT_CONFIG)

    setup_logging(config['logfile'], config['foreground'], config['debug'])
    silence_loggers(['urllib3'], logging.WARNING)

    user = config.get('user')
    if user:
        change_user(user)

    xivo_dao.init_db_from_config(config)

    token_renewer = TokenRenewer(_new_auth_client(config))
    config['agentd']['client'] = AgentdClient(**config['agentd'])
    config['confd']['client'] = ConfdClient(**config['confd'])
    config['dird']['client'] = DirdClient(**config['dird'])

    def on_token_change(token_id):
        config['agentd']['client'].set_token(token_id)
        config['confd']['client'].set_token(token_id)
        config['dird']['client'].set_token(token_id)
    token_renewer.subscribe_to_token_change(on_token_change)

    with pidfile_context(config['pidfile'], config['foreground']):
        agid.init(config)
        with token_renewer:
            agid.run()


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file', action='store', help='The path to the config file')
    parser.add_argument('-f', action='store_true', dest='foreground',
                        help='run in foreground')
    parser.add_argument('-d', action='store_true', dest='debug',
                        help='increase verbosity')
    parser.add_argument('-u', '--user', action='store', help='User to run the daemon')

    parsed_args = parser.parse_args()

    config = {}
    if parsed_args.config_file:
        config['config_file'] = parsed_args.config_file
    if parsed_args.debug:
        config['debug'] = parsed_args.debug
    if parsed_args.foreground:
        config['foreground'] = parsed_args.foreground
    if parsed_args.user:
        config['user'] = parsed_args.user

    return config


def _load_key_file(config):
    key_file = parse_config_file(config['auth']['key_file'])
    return {'auth': {'service_id': key_file['service_id'],
                     'service_key': key_file['service_key']}}


def _new_auth_client(config):
    auth_config = config['auth']
    return AuthClient(auth_config['host'],
                      port=auth_config['port'],
                      username=auth_config['service_id'],
                      password=auth_config['service_key'],
                      verify_certificate=auth_config['verify_certificate'])


if __name__ == '__main__':
    main()
