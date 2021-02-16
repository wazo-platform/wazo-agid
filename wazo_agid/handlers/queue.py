# -*- coding: utf-8 -*-
# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import re

from wazo_agid import objects
from wazo_agid.handlers import handler

AGENT_CHANNEL_RE = re.compile(r'^Local/id-(\d+)@agentcallback-[a-f0-9]+;1$')


class AnswerHandler(handler.Handler):
    def execute(self):
        try:
            callee = self.get_user()
        except LookupError as e:
            self._agi.verbose(e)
            return

        self.record_call(callee)

    def get_user(self):
        channel_name = self._agi.env['agi_channel']
        search_params = {}

        result = AGENT_CHANNEL_RE.match(channel_name)
        if result:
            agent_id = result.group(1)
            search_params = {'agent_id': int(agent_id)}
        else:
            user_uuid = self._agi.get_variable('XIVO_USERUUID')
            if user_uuid:
                search_params = {'xid': user_uuid}

        if search_params:
            return objects.User(self._agi, self._cursor, **search_params)

        raise LookupError('Failed to find a matching user from {}'.format(channel_name))

    def record_call(self, callee):
        recording_is_on = self._agi.get_variable('WAZO_CALL_RECORD_ACTIVE') == '1'
        if recording_is_on:
            return

        external = self._agi.get_variable('XIVO_CALLORIGIN') == 'extern'
        internal = not external
        should_record = any([
            internal and callee.call_record_incoming_internal_enabled,
            external and callee.call_record_incoming_external_enabled,
        ])
        if not should_record:
            return

        filename = self._agi.get_variable('XIVO_CALLRECORDFILE')
        self._agi.set_variable('__WAZO_CALL_RECORD_ACTIVE', '1')
        self._agi.appexec('MixMonitor', filename)
