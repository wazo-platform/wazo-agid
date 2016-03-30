# -*- coding: utf-8 -*-

# Copyright (C) 2006-2016 Avencall
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
from xivo_agid import objects


logger = logging.getLogger(__name__)


def phone_get_features(agi, cursor, args):
    userid = agi.get_variable('XIVO_USERID')

    feature_list = objects.ExtenFeatures(agi, cursor)

    try:
        user = objects.User(agi, cursor, int(userid))
    except (ValueError, LookupError), e:
        agi.dp_break(str(e))

    _set_current_forwards(agi, user.id)

    for service in feature_list.FEATURES['services']:
        enable = bool(getattr(feature_list, service[0], 0) and getattr(user, service[1], 0))
        agi.set_variable("XIVO_%s" % service[1].upper(), int(enable))


def _set_current_forwards(agi, user_id):
    forwards = _get_forwards(agi, user_id)
    busy_forward = forwards['busy']
    agi.set_variable('XIVO_ENABLEBUSY', _extract_and_format_enabled(busy_forward))
    agi.set_variable('XIVO_DESTBUSY', _extract_and_format_destination(busy_forward))
    noanswer_forward = forwards['noanswer']
    agi.set_variable('XIVO_ENABLERNA', _extract_and_format_enabled(noanswer_forward))
    agi.set_variable('XIVO_DESTRNA', _extract_and_format_destination(noanswer_forward))
    unconditional_forward = forwards['unconditional']
    agi.set_variable('XIVO_ENABLEUNC', _extract_and_format_enabled(unconditional_forward))
    agi.set_variable('XIVO_DESTUNC', _extract_and_format_destination(unconditional_forward))


def _extract_and_format_enabled(forward):
    return int(forward['enabled'])


def _extract_and_format_destination(forward):
    return forward['destination'] if forward['destination'] is not None else ''


def _get_forwards(agi, user_id):
    try:
        confd_client = agi.config['confd']['client']
        return confd_client.users(user_id).list_forwards()
    except Exception as e:
        logger.error('Error during getting forwards: %s', e)
        return {'busy': {'enabled': False, 'destination': None},
                'noanswer': {'enabled': False, 'destination': None},
                'unconditional': {'enabled': False, 'destination': None}}

agid.register(phone_get_features)
