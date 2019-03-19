# -*- coding: utf-8 -*-
# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import itertools
import logging

from requests import HTTPError
from xivo_agid import agid

logger = logging.getLogger(__name__)


class GroupMemberError(Exception):
    pass


class UnknownLine(GroupMemberError):
    pass


class UnknownUser(GroupMemberError):
    pass


def group_member_add(agi, cursor, args):
    user_uuid = args[0]
    group_id = int(args[1])

    confd_client = agi.config['confd']['client']

    group_name = _get_group(confd_client, group_id)['name']

    interfaces = _get_user_interfaces(agi, user_uuid)

    for interface in interfaces:
        agi.appexec('AddQueueMember', '{group},{interface}'.format(group=group_name, interface=interface))


def group_member_remove(agi, cursor, args):
    user_uuid = args[0]
    group_id = int(args[1])

    confd_client = agi.config['confd']['client']

    group_name = _get_group(confd_client, group_id)['name']

    interfaces = _get_user_interfaces(agi, user_uuid)

    for interface in interfaces:
        agi.appexec('RemoveQueueMember', '{group},{interface}'.format(group=group_name, interface=interface))


def group_member_present(agi, cursors, args):
    user_uuid = args[0]
    group_id = int(args[1])

    confd_client = agi.config['confd']['client']

    group_name = _get_group(confd_client, group_id)['name']

    group_members = agi.get_variable('QUEUE_MEMBER_LIST({group})'.format(group=group_name))
    group_members = group_members.split(',')

    interfaces = _get_user_interfaces(agi, user_uuid)

    if set(interfaces).intersection(set(group_members)):
        agi.set_variable('WAZO_GROUP_MEMBER_PRESENT', '1')
    else:
        agi.set_variable('WAZO_GROUP_MEMBER_PRESENT', '0')


def _get_group(confd_client, group_id):
    return confd_client.groups.get(group_id)


def _get_user_interfaces(agi, user_uuid):
    confd_client = agi.config['confd']['client']
    try:
        lines = confd_client.users.get(user_uuid)['lines']
    except HTTPError as e:
        if e.response and e.response.status_code == 404:
            raise UnknownUser()
        raise

    interfaces = list(itertools.chain(*(_get_line_interfaces(agi, line) for line in lines)))

    return interfaces


def _get_line_interfaces(agi, line):
    if line['endpoint_sip']:
        contacts = agi.get_variable('PJSIP_DIAL_CONTACTS({name})'.format(name=line['endpoint_sip']['username']))
        contacts = contacts.split('&')
        return contacts

    if line['endpoint_sccp']:
        return ['SCCP/{name}'.format(name=line['name'])]

    return []


agid.register(group_member_remove)
agid.register(group_member_add)
agid.register(group_member_present)
