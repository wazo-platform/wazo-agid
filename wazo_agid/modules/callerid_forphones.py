# -*- coding: utf-8 -*-
# Copyright 2012-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from requests.exceptions import RequestException
from wazo_agid import agid
from xivo_dao.resources.directory_profile import dao as directory_profile_dao

logger = logging.getLogger(__name__)

FAKE_XIVO_USER_UUID = '00000000-0000-0000-0000-000000000000'


def callerid_forphones(agi, cursor, args):
    dird_client = agi.config['dird']['client']
    try:
        cid_name = agi.env['agi_calleridname']
        cid_number = agi.env['agi_callerid']

        logger.debug('Resolving caller ID: incoming caller ID=%s %s', cid_name, cid_number)
        if not _should_reverse_lookup(cid_name, cid_number):
            return

        incall_id = int(agi.get_variable('XIVO_INCALL_ID'))
        callee_infos = directory_profile_dao.find_by_incall_id(incall_id)
        if callee_infos is None:
            xivo_user_uuid = FAKE_XIVO_USER_UUID
        else:
            xivo_user_uuid = callee_infos.xivo_user_uuid

        tenant_uuid = agi.get_variable('WAZO_TENANT_UUID')
        try:
            # It is not possible to associate a profile to a reverse configuration in the webi
            lookup_result = dird_client.directories.reverse(
                profile='default',
                xivo_user_uuid=xivo_user_uuid,
                exten=cid_number,
                tenant_uuid=tenant_uuid,
            )
        except RequestException as e:
            logger.exception('Reverse lookup failed: %s', e)
        else:
            logger.debug('Found caller ID: "%s"<%s>', lookup_result['display'], cid_number)
            if lookup_result['display'] is not None:
                _set_new_caller_id(agi, lookup_result['display'], cid_number)
                _set_reverse_lookup_variable(agi, lookup_result['fields'])
    except Exception:
        logger.exception('Reverse lookup failed')


def _should_reverse_lookup(cid_name, cid_number):
    return cid_name == cid_number or cid_name == 'unknown'


def _set_new_caller_id(agi, display_name, cid_number):
    new_caller_id = u'"{}" <{}>'.format(display_name, cid_number)
    agi.set_callerid(new_caller_id.encode('utf8'))


def _set_reverse_lookup_variable(agi, fields):
    agi.set_variable("XIVO_REVERSE_LOOKUP", _create_reverse_lookup_variable(fields))


def _create_reverse_lookup_variable(fields):
    variable_content = []
    for key, value in fields.iteritems():
        variable_content.append(u'db-{}: {}'.format(key, value))

    return u','.join(variable_content).encode('utf8')


agid.register(callerid_forphones)
