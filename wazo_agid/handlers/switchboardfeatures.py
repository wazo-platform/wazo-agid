# Copyright 2021-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from xivo_dao.alchemy import Switchboard
from xivo_dao.resources.switchboard import dao as switchboard_dao
from xivo_dao.helpers.exception import NotFoundError
from wazo_agid.handlers.handler import Handler


class SwitchboardFeatures(Handler):
    def __init__(self, agi, cursor, args):
        super().__init__(agi, cursor, args)
        self.switchboard_uuid: str | None = None
        self.switchboard: Switchboard = None  # type: ignore[assignment]

    def execute(self):
        self._extract_switchboard_uuid()
        self._set_switchboard()
        self._set_fallback_destination()

    def _extract_switchboard_uuid(self):
        try:
            self.switchboard_uuid = self._args[0]
        except IndexError:
            self._agi.dp_break('Missing feature switchboard_uuid argument')

    def _set_switchboard(self):
        try:
            self.switchboard = switchboard_dao.get(self.switchboard_uuid)
        except NotFoundError as e:
            self._agi.dp_break(str(e))

    def _set_fallback_destination(self):
        self._agi.set_variable('WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTION', '')
        self._agi.set_variable('WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTIONARG1', '')
        self._agi.set_variable('WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTIONARG2', '')

        noanswer_fallback = self.switchboard.fallbacks.get('noanswer')
        if noanswer_fallback:
            self._agi.set_variable(
                'WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTION', noanswer_fallback.action
            )
            self._agi.set_variable(
                'WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTIONARG1',
                noanswer_fallback.actionarg1,
            )
            self._agi.set_variable(
                'WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTIONARG2',
                noanswer_fallback.actionarg2,
            )

        self._agi.set_variable('WAZO_SWITCHBOARD_TIMEOUT', self.switchboard.timeout)
