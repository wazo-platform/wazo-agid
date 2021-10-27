# -*- coding: utf-8 -*-
# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import re

from wazo_agid import agid, objects


MEETING_RE = re.compile(r'^wazo-meeting-([0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})$')


def meeting_user(agi, cursor, args):
    tenant_uuid = agi.get_variable('WAZO_TENANT_UUID')
    if not args:
        return _fail(agi, args)
    try:
        matches = MEETING_RE.match(args[0])
    except TypeError:
        return _fail(agi, args)

    meeting_uuid = matches.group(1) if matches else None
    try:
        meeting = objects.Meeting(agi, cursor, tenant_uuid, meeting_uuid)
    except LookupError:
        return _fail(agi, args)

    agi.set_variable('WAZO_MEETING_UUID', meeting_uuid)
    agi.set_variable('WAZO_MEETING_NAME', meeting.name)


def _fail(agi, args):
    agi.answer()
    agi.stream_file('invalid')
    agi.dp_break('Could not find meeting matching {}'.format(args))


agid.register(meeting_user)
