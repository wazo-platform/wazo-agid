# Copyright 2019-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import uuid

from datetime import datetime, timezone

from psycopg2.extras import DictCursor

from wazo_agid import agid

logger = logging.getLogger(__name__)


def wake_mobile(agi: agid.FastAGI, cursor: DictCursor, args: list[str]) -> None:
    user_uuid = args[0]
    should_wake_mobile = agi.get_variable('WAZO_WAIT_FOR_MOBILE') or False

    if not should_wake_mobile:
        return

    video_enabled = agi.get_variable('WAZO_VIDEO_ENABLED')
    ring_time = (
        agi.get_variable('WAZO_RING_TIME') or agi.get_variable('WAZO_RINGSECONDS') or 30
    )
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    push_trace_uuid = str(uuid.uuid4())

    logger.info(
        'Sending Pushmobile for user %s push_trace_uuid=%s',
        user_uuid,
        push_trace_uuid,
    )
    agi.appexec(
        'UserEvent',
        f'Pushmobile,WAZO_DST_UUID: {user_uuid},WAZO_VIDEO_ENABLED: {video_enabled},'
        f'WAZO_RING_TIME: {ring_time},'
        f'WAZO_TIMESTAMP: {timestamp},'
        f'WAZO_PUSH_TRACE_UUID: {push_trace_uuid}',
    )


agid.register(wake_mobile)
