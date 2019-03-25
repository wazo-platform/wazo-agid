# -*- coding: utf-8 -*-
# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import itertools
import logging

from requests import HTTPError
from xivo_agid import agid

logger = logging.getLogger(__name__)


class UnknownUser(Exception):
    pass


def get_user_interfaces(agi, cursor, args):
    user_uuid = args[0]

    confd_client = agi.config['confd']['client']
    try:
        lines = confd_client.users.get(user_uuid)['lines']
    except HTTPError as e:
        if e.response and e.response.status_code == 404:
            raise UnknownUser()
        raise

    interfaces = list(itertools.chain(*(_get_line_interfaces(agi, line) for line in lines)))

    agi.set_variable('WAZO_USER_INTERFACES', '{interfaces}'.format(interfaces='&'.join(interfaces)))


def _get_line_interfaces(agi, line):
    if line['endpoint_sip']:
        contacts = agi.get_variable('PJSIP_DIAL_CONTACTS({name})'.format(name=line['endpoint_sip']['username']))
        if contacts:
            return contacts.split('&')

    if line['endpoint_sccp']:
        return ['SCCP/{name}'.format(name=line['name'])]

    if line['endpoint_custom']:
        return [line['endpoint_custom']['interface']]

    return []


agid.register(get_user_interfaces)
