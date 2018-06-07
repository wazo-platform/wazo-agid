# -*- coding: utf-8 -*-
# Copyright (C) 2012-2016 Avencall
# SPDX-License-Identifier: GPL-3.0+

from xivo_agentd_client import error
from xivo_agentd_client.error import AgentdClientError

AGENTSTATUS_VAR = 'XIVO_AGENTSTATUS'


def login_agent(agi, agent_id, extension, context):
    agentd_client = agi.config['agentd']['client']
    try:
        agentd_client.agents.login_agent(agent_id, extension, context)
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
    agentd_client = agi.config['agentd']['client']
    try:
        agentd_client.agents.logoff_agent(agent_id)
    except AgentdClientError as e:
        if e.error != error.NOT_LOGGED:
            raise


def get_agent_status(agi, agent_id):
    agentd_client = agi.config['agentd']['client']
    status = agentd_client.agents.get_agent_status(agent_id)
    login_status = 'logged_in' if status.logged else 'logged_out'
    agi.set_variable('XIVO_AGENT_LOGIN_STATUS', login_status)
