# -*- coding: utf-8 -*-
# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import itertools
import logging

from contextlib import contextmanager
from requests import RequestException
from xivo_agid import agid

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
        with _confd_tenant(confd_client, tenant_uuid):
            group_name = confd_client.groups.get(group_id)['name']
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
        with _confd_tenant(confd_client, tenant_uuid):
            group_name = confd_client.groups.get(group_id)['name']
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
        with _confd_tenant(confd_client, tenant_uuid):
            group_name = confd_client.groups.get(group_id)['name']
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
    confd_client = agi.config['confd']['client']
    lines = confd_client.users.get(user_uuid)['lines']

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


@contextmanager
def _confd_tenant(confd_client, tenant_uuid):
    confd_client.set_tenant(tenant_uuid)
    try:
        yield
    finally:
        confd_client.set_tenant(None)


agid.register(group_member_remove)
agid.register(group_member_add)
agid.register(group_member_present)
