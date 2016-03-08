# -*- coding: utf-8 -*-

# Copyright (C) 2011-2016 Avencall
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

import logging
from xivo_agid import agid
from xivo_confd_client import Client

logger = logging.getLogger(__name__)

TIMEOUT = 10


def _do_provision(client, provcode, ip):
    device = _get_device(client, ip)
    line = _get_line(client, provcode)
    client.lines(line).add_device(device)
    client.devices.synchronize(device['id'])


def _get_device(client, ip):
    response = client.devices.list(ip=ip)
    if response['total'] != 1:
        raise Exception("Device with ip {} not found".format(ip))
    return response['items'][0]


def _get_line(client, provcode):
    response = client.lines.list(provisioning_code=provcode)
    if response['total'] != 1:
        raise Exception("Line with provisioning code {} not found".format(provcode))
    return response['items'][0]


def provision(agi, cursor, args):
    try:
        confd_config = dict(agi.config['confd'])
        client = Client(token=agi.config['auth']['token'], **confd_config)
        provcode = args[0]
        ip = args[1]
        _do_provision(client, provcode, ip)
    except Exception, e:
        logger.error('Error during provisioning: %s', e)
    else:
        agi.set_variable('XIVO_PROV_OK', '1')


agid.register(provision)
