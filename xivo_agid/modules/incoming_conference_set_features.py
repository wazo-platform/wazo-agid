# -*- coding: utf-8 -*-

# Copyright 2016 The Wazo Authors  (see the AUTHORS file)
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

from xivo_agid import agid
from xivo_dao.resources.conference import dao as conference_dao


CONFBRIDGE_RECORDINGDIR = '/var/lib/asterisk/sounds/confbridge'


def incoming_conference_set_features(agi, cursor, args):
    conference_id = int(agi.get_variable('XIVO_DSTID'))

    try:
        conference = conference_dao.get(conference_id)
    except (ValueError), e:
        agi.dp_break(str(e))

    menu = 'xivo-default-user-menu'
    user_profile = 'xivo-user-profile-{}'.format(conference.id)
    if conference.pin:
        for _ in range(4):
            agi.answer()
            pin = agi.get_data('conf-getpin', 10000, 80)
            if pin == conference.pin:
                break
            elif pin == conference.admin_pin:
                menu = 'xivo-default-admin-menu'
                user_profile = 'xivo-admin-profile-{}'.format(conference.id)
                break
            else:
                agi.stream_file('conf-invalidpin')
        else:
            agi.dp_break("Unable to join the conference room, wrong pin"
                         "(conference_id: {}, name: {})".format(conference.id, conference.name))

    agi.set_variable('XIVO_CONFBRIDGE_ID', conference.id)
    agi.set_variable('XIVO_CONFBRIDGE_BRIDGE_PROFILE', 'xivo-bridge-profile-{}'.format(conference.id))
    agi.set_variable('XIVO_CONFBRIDGE_USER_PROFILE', user_profile)
    agi.set_variable('XIVO_CONFBRIDGE_MENU', menu)
    agi.set_variable('XIVO_CONFBRIDGE_PREPROCESS_SUBROUTINE', conference.preprocess_subroutine or '')


agid.register(incoming_conference_set_features)
