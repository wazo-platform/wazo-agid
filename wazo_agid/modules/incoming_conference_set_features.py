# -*- coding: utf-8 -*-
# Copyright 2016-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_agid import agid
from xivo_dao.resources.conference import dao as conference_dao


def incoming_conference_set_features(agi, cursor, args):
    conference_id = int(agi.get_variable('XIVO_DSTID'))

    try:
        conference = conference_dao.get(conference_id)
    except (ValueError) as e:
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

    agi.set_variable('WAZO_CONFBRIDGE_ID', conference.id)
    agi.set_variable('WAZO_CONFBRIDGE_TENANT_UUID', conference.tenant_uuid)
    agi.set_variable('WAZO_CONFBRIDGE_BRIDGE_PROFILE', 'xivo-bridge-profile-{}'.format(conference.id))
    agi.set_variable('WAZO_CONFBRIDGE_USER_PROFILE', user_profile)
    agi.set_variable('WAZO_CONFBRIDGE_MENU', menu)
    agi.set_variable('WAZO_CONFBRIDGE_PREPROCESS_SUBROUTINE', conference.preprocess_subroutine or '')


agid.register(incoming_conference_set_features)
