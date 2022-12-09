# Copyright 2021-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import re

from wazo_agid import objects
from wazo_agid.handlers import handler

logger = logging.getLogger(__name__)

EXTEN_CONTEXT_RE = re.compile(r'^Local/(.+)@(.+)-[a-f0-9]+;1$')


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

        result = EXTEN_CONTEXT_RE.match(channel_name)
        if result:
            exten = result.group(1)
            context = result.group(2)
            if context == 'usersharedlines':
                search_params = {'xid': exten}
            else:
                search_params = {'exten': exten, 'context': context}

            return objects.User(self._agi, self._cursor, **search_params)

        raise LookupError(f'Failed to find a matching user from {channel_name}')

    def record_call(self, callee):
        recording_is_on = self._agi.get_variable('WAZO_CALL_RECORD_ACTIVE') == '1'
        if recording_is_on:
            return

        external = self._agi.get_variable('XIVO_CALLORIGIN') == 'extern'
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
        self._agi.set_variable('WAZO_RECORD_GROUP_CALLEE', '1')
        try:
            calld.calls.start_record(channel_id)
        except Exception as e:
            logger.error('Error during enabling call recording: %s', e)
