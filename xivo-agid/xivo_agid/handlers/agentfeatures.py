# -*- coding: utf-8 -*-

# Copyright (C) 2013-2014 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from xivo_agid import objects
from xivo_agid.handlers.handler import Handler


class AgentFeatures(Handler):

    def __init__(self, agi, cursor, args):
        Handler.__init__(self, agi, cursor, args)
        self.agent_id = None
        self.agent = None

    def execute(self):
        self._extract_agent_id()
        self._set_agent_interface()
        self._set_agent()
        self._set_preprocess_subroutine()

    def _extract_agent_id(self):
        try:
            self.agent_id = self._args[0]
        except IndexError:
            self._agi.dp_break('Missing feature agent_id argument')

    def _set_agent_interface(self):
        try:
            device = self._get_agent_device()
        except LookupError as e:
            self._agi.dp_break(str(e))
        self._agi.set_variable('XIVO_AGENT_INTERFACE', device)

    def _get_agent_device(self):
        self._cursor.query('SELECT state_interface FROM agent_login_status WHERE agent_id  = %s',
                           parameters=(self.agent_id,))
        res = self._cursor.fetchone()
        if not res:
            raise LookupError('Unable to find agent (id: %s)' % self.agent_id)
        device = res[0]
        return device

    def _set_agent(self):
        try:
            self.agent = objects.Agent(self._agi, self._cursor, self.agent_id)
        except (LookupError, IndexError) as e:
            self._agi.dp_break(str(e))

    def _set_preprocess_subroutine(self):
        if self.agent.preprocess_subroutine:
            preprocess_subroutine = self.agent.preprocess_subroutine
        else:
            preprocess_subroutine = ''
        self._agi.set_variable('XIVO_AGENTPREPROCESS_SUBROUTINE', preprocess_subroutine)
