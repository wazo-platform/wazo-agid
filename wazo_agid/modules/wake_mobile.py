# Copyright 2019-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from psycopg2.extras import DictCursor

from wazo_agid import agid


def wake_mobile(agi: agid.FastAGI, cursor: DictCursor, args: list[str]) -> None:
    user_uuid = args[0]
    should_wake_mobile = agi.get_variable('WAZO_WAIT_FOR_MOBILE') or False

    if not should_wake_mobile:
        return

    video_enabled = agi.get_variable('WAZO_VIDEO_ENABLED')
    ring_time = agi.get_variable('XIVO_RINGSECONDS') or 30
    agi.appexec(
        'UserEvent',
        f'Pushmobile,WAZO_DST_UUID: {user_uuid},WAZO_VIDEO_ENABLED: {video_enabled},WAZO_RING_TIME: {ring_time}',
    )


agid.register(wake_mobile)
