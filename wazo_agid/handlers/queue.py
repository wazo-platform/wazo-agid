# Copyright 2021-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import re

from wazo_agid import objects
from wazo_agid.handlers import handler

logger = logging.getLogger(__name__)

AGENT_CHANNEL_RE = re.compile(r'^Local/id-(\d+)@agentcallback-[a-f0-9]+;1$')


class AnswerHandler(handler.Handler):
    def execute(self):
        try:
            callee = self.get_user()
        except LookupError as e:
            self._agi.verbose(e)
            return

        self.record_call(callee)

    def get_user(self) -> objects.User:
        channel_name = self._agi.env['agi_channel']
        search_params: dict[str, str | int] = {}

        result = AGENT_CHANNEL_RE.match(channel_name)
        if result:
            agent_id = result.group(1)
            search_params = {'agent_id': int(agent_id)}
        else:
            user_uuid = self._agi.get_variable('WAZO_USERUUID')
            if user_uuid:
                search_params = {'xid': user_uuid}

        if search_params:
            return objects.User(self._agi, self._cursor, **search_params)

        raise LookupError(f'Failed to find a matching user from {channel_name}')

    def record_call(self, callee: objects.User) -> None:
        recording_is_on = self._agi.get_variable('WAZO_CALL_RECORD_ACTIVE') == '1'
        if recording_is_on:
            return

        external = self._agi.get_variable('WAZO_CALLORIGIN') == 'extern'
        internal = not external
        should_record = any(
            [
                internal and callee.call_record_incoming_internal_enabled,
                external and callee.call_record_incoming_external_enabled,
            ]
        )
        if not should_record:
            return

        calld = self._agi.config['calld']['client']
        channel_id = self._agi.env['agi_uniqueid']
        tenant_uuid = self._agi.get_variable('WAZO_TENANT_UUID')
        try:
            calld.calls.start_record(channel_id, tenant_uuid=tenant_uuid)
        except Exception as e:
            logger.error('Error during enabling call recording: %s', e)
