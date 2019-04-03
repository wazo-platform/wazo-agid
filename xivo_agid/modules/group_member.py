# -*- coding: utf-8 -*-
# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging

from requests import RequestException
from xivo_agid import (
    agid,
    objects,
)

logger = logging.getLogger(__name__)


class GroupMemberError(Exception):
    pass


class UnknownUser(GroupMemberError):
    pass


def group_member_add(agi, cursor, args):
    tenant_uuid = args[0]
    user_uuid = args[1]
    group_id = int(args[2])

    confd_client = agi.config['confd']['client']

    try:
        group_name = confd_client.groups.get(group_id, tenant_uuid=tenant_uuid)['name']
    except RequestException as e:
        logger.error('Error while getting group %s in tenant %s: %s', group_id, tenant_uuid, e)
        agi.set_variable('WAZO_GROUP_MEMBER_ERROR', e)
        return

    try:
        interfaces = _get_user_interfaces(agi, user_uuid)
    except RequestException as e:
        logger.error('Error while getting user interfaces: %s', e)
        agi.set_variable('WAZO_GROUP_MEMBER_ERROR', e)
        return

    for interface in interfaces:
        agi.appexec('AddQueueMember', '{group},{interface}'.format(group=group_name, interface=interface))


def group_member_remove(agi, cursor, args):
    tenant_uuid = args[0]
    user_uuid = args[1]
    group_id = int(args[2])

    confd_client = agi.config['confd']['client']

    try:
        group_name = confd_client.groups.get(group_id, tenant_uuid=tenant_uuid)['name']
    except RequestException as e:
        logger.error('Error while getting group %s in tenant %s: %s', group_id, tenant_uuid, e)
        agi.set_variable('WAZO_GROUP_MEMBER_ERROR', e)
        return

    try:
        interfaces = _get_user_interfaces(agi, user_uuid)
    except RequestException as e:
        logger.error('Error while getting user interfaces: %s', e)
        agi.set_variable('WAZO_GROUP_MEMBER_ERROR', e)
        return

    for interface in interfaces:
        agi.appexec('RemoveQueueMember', '{group},{interface}'.format(group=group_name, interface=interface))


def group_member_present(agi, cursors, args):
    tenant_uuid = args[0]
    user_uuid = args[1]
    group_id = int(args[2])

    confd_client = agi.config['confd']['client']

    try:
        group_name = confd_client.groups.get(group_id, tenant_uuid=tenant_uuid)['name']
    except RequestException as e:
        logger.error('Error while getting group %s in tenant %s: %s', group_id, tenant_uuid, e)
        agi.set_variable('WAZO_GROUP_MEMBER_ERROR', e)
        return

    group_members = agi.get_variable('QUEUE_MEMBER_LIST({group})'.format(group=group_name))
    group_members = group_members.split(',')

    interfaces = _get_user_interfaces(agi, user_uuid)

    if set(interfaces).intersection(set(group_members)):
        agi.set_variable('WAZO_GROUP_MEMBER_PRESENT', '1')
    else:
        agi.set_variable('WAZO_GROUP_MEMBER_PRESENT', '0')


def _get_user_interfaces(agi, user_uuid):
    user_line = objects.UserLine(agi, user_uuid)
    return user_line.interfaces


agid.register(group_member_remove)
agid.register(group_member_add)
agid.register(group_member_present)
