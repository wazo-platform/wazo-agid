# -*- coding: utf-8 -*-
# Copyright 2019-2020 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_agid import agid


def wake_mobile(agi, cursor, args):
    should_wake_mobile = agi.get_variable('WAZO_WAIT_FOR_MOBILE') or False
    if not should_wake_mobile:
        return

    user_uuid = agi.get_variable('WAZO_DST_UUID')
    video_enabled = agi.get_variable('WAZO_VIDEO_ENABLED')
    agi.appexec('UserEvent', 'Pushmobile,WAZO_DST_UUID: {},WAZO_VIDEO_ENABLED: {}'.format(user_uuid, video_enabled))


agid.register(wake_mobile)
