# -*- coding: utf-8 -*-
# Copyright (C) 2013-2016 Avencall
# SPDX-License-Identifier: GPL-3.0+

import re

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
        self._set_queue_call_options()

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

    def _set_queue_call_options(self):
        queue_options = self._agi.get_variable('XIVO_QUEUEOPTIONS')
        queue_call_options = self._extract_queue_call_options(queue_options)
        self._agi.set_variable('XIVO_QUEUECALLOPTIONS', queue_call_options)

    def _extract_queue_call_options(self, queue_options):
        queue_options = re.sub(r'\(.*?\)', '', queue_options)
        authorized_options = ['h', 'i', 't', 'w', 'x', 'k']
        queue_call_options = ''
        for option in queue_options:
            if option in authorized_options:
                queue_call_options += option
        return queue_call_options
