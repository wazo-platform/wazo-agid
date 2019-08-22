# -*- coding: utf-8 -*-
# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_agid import agid


def wake_mobile(agi, cursor, args):
    should_wake_mobile = agi.get_variable('WAZO_WAIT_FOR_MOBILE') or False
    if not should_wake_mobile:
        return

    user_uuid = agi.get_variable('WAZO_DST_UUID')
    agi.appexec('UserEvent', 'Pushmobile,WAZO_DST_UUID: {}'.format(user_uuid))


agid.register(wake_mobile)
