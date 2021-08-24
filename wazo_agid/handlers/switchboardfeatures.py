# -*- coding: utf-8 -*-
# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from xivo_dao.resources.switchboard import dao as switchboard_dao
from wazo_agid.handlers.handler import Handler


class SwitchboardFeatures(Handler):

    def __init__(self, agi, cursor, args):
        Handler.__init__(self, agi, cursor, args)
        self.switchboard_uuid = None
        self.switchboard = None

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
        except (LookupError, IndexError) as e:
            self._agi.dp_break(str(e))

    def _set_fallback_destination(self):
        noanswer_fallback = self.switchboard.fallbacks.get('noanswer')
        if noanswer_fallback:
            self._set_variable('WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTION', noanswer_fallback.action)
            self._set_variable('WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTIONARG1', noanswer_fallback.actionarg1)
            self._set_variable('WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTIONARG2', noanswer_fallback.actionarg2)

        self._set_variable('WAZO_SWITCHBOARD_TIMEOUT', self.switchboard.timeout)

    def _set_variable(self, variable, value):
        if value:
            self._agi.set_variable(variable, value)
        else:
            # when forwarding across multiple switchboard, previous switchboards
            # must not affect the current fallbacks
            self._agi.set_variable(variable, '')
