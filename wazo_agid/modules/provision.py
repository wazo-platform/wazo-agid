# Copyright 2011-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from wazo_agid import agid
from wazo_agid import dialplan_variables as dv

if TYPE_CHECKING:
    from psycopg2.extras import DictCursor
    from wazo_confd_client.client import ConfdClient


logger = logging.getLogger(__name__)

TIMEOUT = 10


def _do_provision(client: ConfdClient, provcode: str, ip: str) -> None:
    if provcode == "autoprov":
        logger.debug(f"putting device with ip {ip} in autoprov mode")
        device = _get_device(client, ip)
        logger.debug(f"device found: {device}")
        client.devices.autoprov(device['id'])
    else:
        logger.debug(
            f"adding device with ip {ip} to line with provisioning code {provcode}"
        )
        line = _get_line(client, provcode)
        logger.debug(f"line found: {line}")
        device = _get_device(client, ip, only_autoprov=True)
        logger.debug(f"device found: {device}")
        client.lines(line).add_device(device)
    client.devices.synchronize(device['id'])


def _get_device(
    client: ConfdClient, ip: str, only_autoprov: bool = False
) -> dict[str, Any]:
    if only_autoprov:
        response = client.devices.list(ip=ip, search='autoprov', recurse=True)
    else:
        response = client.devices.list(ip=ip, recurse=True)

    if response['total'] != 1:
        raise Exception(f"Device with ip {ip} not found")
    return response['items'][0]


def _get_line(client: ConfdClient, provcode: str) -> dict[str, Any]:
    response = client.lines.list(provisioning_code=provcode, recurse=True)
    if response['total'] != 1:
        raise Exception(f"Line with provisioning code {provcode} not found")
    return response['items'][0]


def provision(agi: agid.FastAGI, cursor: DictCursor, args: list[str]) -> None:
    try:
        client = agi.config['confd']['client']
        provcode = args[0]
        ip_port = args[1]
        if ':' in ip_port:
            ip, _ = ip_port.split(':', 1)
        else:
            ip = ip_port
        _do_provision(client, provcode, ip)
    except Exception as e:
        logger.error('Error during provisioning: %s', e)
    else:
        agi.set_variable(dv.PROV_OK, '1')


agid.register(provision)
