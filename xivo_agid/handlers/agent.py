# -*- coding: utf-8 -*-

# Copyright (C) 2012-2015 Avencall
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

from functools import partial

from xivo import moresynchro
from xivo_agentd_client import Client as AgentdClient, error
from xivo_agentd_client.error import AgentdClientError

AGENTSTATUS_VAR = 'XIVO_AGENTSTATUS'

_agentd_client = None
_once = moresynchro.Once()


def _init_client(config):
    global _agentd_client

    agentd_cfg_dict = config['agentd']
    _agentd_client = AgentdClient(**agentd_cfg_dict)


def login_agent(agi, agent_id, extension, context):
    _once.once(partial(_init_client, agi.config))
    try:
        _agentd_client.agents.login_agent(agent_id, extension, context)
    except AgentdClientError as e:
        if e.error == error.ALREADY_LOGGED:
            agi.set_variable(AGENTSTATUS_VAR, 'already_logged')
        elif e.error == error.ALREADY_IN_USE:
            agi.set_variable(AGENTSTATUS_VAR, 'already_in_use')
        else:
            raise
    else:
        agi.set_variable(AGENTSTATUS_VAR, 'logged')


def logoff_agent(agi, agent_id):
    _once.once(partial(_init_client, agi.config))
    try:
        _agentd_client.agents.logoff_agent(agent_id)
    except AgentdClientError as e:
        if e.error != error.NOT_LOGGED:
            raise


def get_agent_status(agi, agent_id):
    _once.once(partial(_init_client, agi.config))
    status = _agentd_client.agents.get_agent_status(agent_id)
    login_status = 'logged_in' if status.logged else 'logged_out'
    agi.set_variable('XIVO_AGENT_LOGIN_STATUS', login_status)
