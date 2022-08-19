# Copyright 2021-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import re

from wazo_agid import agid, objects


MEETING_RE = re.compile(
    r'^wazo-meeting-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$'
)


def meeting_user(agi, cursor, args):
    tenant_uuid = agi.get_variable('WAZO_TENANT_UUID')
    try:
        meeting = _find_meeting(agi, cursor, tenant_uuid, args)
    except (AttributeError, LookupError, TypeError) as e:
        agi.verbose('Failed to find meeting {}'.format(e))
        agi.answer()
        agi.stream_file('invalid')
        return agi.dp_break('Could not find meeting matching {}'.format(args))

    agi.set_variable('WAZO_MEETING_UUID', meeting.uuid)
    agi.set_variable('WAZO_MEETING_NAME', meeting.name)


def _find_meeting(agi, cursor, tenant_uuid, args):
    identifier = args[0]

    if identifier.isdigit():
        return objects.Meeting(agi, cursor, tenant_uuid, number=identifier)
    else:
        matches = MEETING_RE.match(identifier)
        return objects.Meeting(agi, cursor, tenant_uuid, uuid=matches.group(1))


agid.register(meeting_user)
