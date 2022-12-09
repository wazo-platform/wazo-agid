# Copyright 2012-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from wazo_agid import agid
from xivo_dao.resources.directory_profile import dao as directory_profile_dao

logger = logging.getLogger(__name__)

FAKE_XIVO_USER_UUID = '00000000-0000-0000-0000-000000000000'


def callerid_forphones(agi, cursor, args):
    dird_client = agi.config['dird']['client']
    try:
        cid_name = agi.env['agi_calleridname']
        cid_number = agi.env['agi_callerid']

        logger.debug(
            'Resolving caller ID: incoming caller ID=%s %s', cid_name, cid_number
        )
        if not _should_reverse_lookup(cid_name, cid_number):
            return

        incall_id = int(agi.get_variable('XIVO_INCALL_ID'))
        callee_infos = directory_profile_dao.find_by_incall_id(incall_id)
        if callee_infos is None:
            user_uuid = FAKE_XIVO_USER_UUID
        else:
            user_uuid = callee_infos.xivo_user_uuid

        tenant_uuid = agi.get_variable('WAZO_TENANT_UUID')
        # It is not possible to associate a profile to a reverse configuration in the web
        lookup_result = dird_client.directories.reverse(
            profile='default',
            user_uuid=user_uuid,
            exten=cid_number,
            tenant_uuid=tenant_uuid,
        )
        logger.debug('Found caller ID: "%s"<%s>', lookup_result['display'], cid_number)
        if lookup_result['display'] is not None:
            _set_new_caller_id(agi, lookup_result['display'], cid_number)
            _set_reverse_lookup_variable(agi, lookup_result['fields'])
    except Exception as e:
        msg = f'Reverse lookup failed: {e}'
        logger.info(msg)
        agi.verbose(msg)


def _should_reverse_lookup(cid_name, cid_number):
    return cid_name == cid_number or cid_name == 'unknown'


def _set_new_caller_id(agi, display_name, cid_number):
    new_caller_id = f'"{display_name}" <{cid_number}>'
    agi.set_callerid(new_caller_id)


def _set_reverse_lookup_variable(agi, fields):
    agi.set_variable("XIVO_REVERSE_LOOKUP", _create_reverse_lookup_variable(fields))


def _create_reverse_lookup_variable(fields):
    variable_content = [f'db-{key}: {value}' for key, value in fields.items()]
    return ','.join(variable_content)


agid.register(callerid_forphones)
