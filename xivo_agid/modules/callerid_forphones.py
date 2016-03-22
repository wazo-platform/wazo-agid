# -*- coding: utf-8 -*-

# Copyright (C) 2012-2016 Avencall
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

from requests.exceptions import RequestException
from xivo_agid import agid
from xivo_dao.resources.directory_profile import dao as directory_profile_dao

logger = logging.getLogger(__name__)

FAKE_XIVO_USER_UUID = '00000000-0000-0000-0000-000000000000'


def callerid_forphones(agi, cursor, args):
    dird_client = agi.config['dird']['client']
    try:
        cid_name = agi.env['agi_calleridname']
        cid_number = agi.env['agi_callerid']

        logger.debug('Resolving caller ID: incoming caller ID=%s %s', cid_name, cid_number)
        if _should_reverse_lookup(cid_name, cid_number):
            incall_id = int(agi.get_variable('XIVO_INCALL_ID'))
            callee_infos = directory_profile_dao.find_by_incall_id(incall_id)
            if callee_infos is None:
                xivo_user_uuid = FAKE_XIVO_USER_UUID
            else:
                xivo_user_uuid = callee_infos.xivo_user_uuid
            try:
                # It is not possible to associate a profile to a reverse configuration in the webi
                lookup_result = dird_client.directories.reverse(profile='default',
                                                                xivo_user_uuid=xivo_user_uuid,
                                                                exten=cid_number)
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
