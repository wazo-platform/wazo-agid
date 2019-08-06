# -*- coding: utf-8 -*-
# Copyright 2011-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from xivo_agid import agid

logger = logging.getLogger(__name__)

TIMEOUT = 10


def _do_provision(client, provcode, ip):
    device = _get_device(client, ip)
    if provcode == "autoprov":
        client.devices.autoprov(device['id'])
    else:
        line = _get_line(client, provcode)
        client.lines(line).add_device(device)
    client.devices.synchronize(device['id'])


def _get_device(client, ip):
    response = client.devices.list(ip=ip, recurse=True)
    if response['total'] != 1:
        raise Exception("Device with ip {} not found".format(ip))
    return response['items'][0]


def _get_line(client, provcode):
    response = client.lines.list(provisioning_code=provcode, recurse=True)
    if response['total'] != 1:
        raise Exception("Line with provisioning code {} not found".format(provcode))
    return response['items'][0]


def provision(agi, cursor, args):
    try:
        client = agi.config['confd']['client']
        provcode = args[0]
        ip_port = args[1]
        if ':' in ip_port:
            ip, _ = ip_port.split(':', 1)
        else:
            ip = ip_port
        _do_provision(client, provcode, ip)
    except Exception, e:
        logger.error('Error during provisioning: %s', e)
    else:
        agi.set_variable('XIVO_PROV_OK', '1')


agid.register(provision)
