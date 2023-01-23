# Copyright 2021-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

import re

from wazo_agid import agid, objects

if TYPE_CHECKING:
    from psycopg2.extras import DictCursor
    from wazo_agid.agid import FastAGI


MEETING_RE = re.compile(
    r'^wazo-meeting-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$'
)


def meeting_user(agi: FastAGI, cursor: DictCursor, args: list[str]):
    tenant_uuid = agi.get_variable('WAZO_TENANT_UUID')
    try:
        meeting = _find_meeting(agi, cursor, tenant_uuid, args)
    except (AttributeError, LookupError, TypeError, ValueError) as e:
        agi.verbose(f'Failed to find meeting {e}')
        agi.answer()
        agi.stream_file('invalid')
        return agi.dp_break(f'Could not find meeting matching {args}')

    agi.set_variable('WAZO_MEETING_UUID', meeting.uuid)
    agi.set_variable('WAZO_MEETING_NAME', meeting.name)


def _find_meeting(
    agi: FastAGI, cursor: DictCursor, tenant_uuid: str, args: list[str]
) -> objects.Meeting:
    identifier = args[0]

    if identifier.isdigit():
        return objects.Meeting(agi, cursor, tenant_uuid, number=identifier)

    match = MEETING_RE.match(identifier)
    if match:
        return objects.Meeting(agi, cursor, tenant_uuid, uuid=match.group(1))
    raise ValueError(f'Invalid identifier: {identifier}')


agid.register(meeting_user)
