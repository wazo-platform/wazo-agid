# -*- coding: UTF-8 -*-

__license__ = """
    Copyright (C) 2012  Avencall

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
from xivo_agid import agid
from xivo_agent.exception import AgentClientError
from xivo_agent.ctl.client import AgentClient
from xivo_agent.ctl import error

logger = logging.getLogger(__name__)

AGENTSTATUS_VAR = 'XIVO_AGENTSTATUS'

agent_client = None


def agent_login(agi, cursor, args):
    try:
        agent_id = int(args[0])
        interface = args[1]

        _do_agent_login(agi, agent_id, interface)
    except Exception as e:
        logger.exception("Error while logging in agent")
        agi.dp_break(e)


def _do_agent_login(agi, agent_id, interface):
    try:
        agent_client.login_agent(agent_id, interface)
    except AgentClientError as e:
        if e.error == error.ALREADY_LOGGED:
            agi.set_variable(AGENTSTATUS_VAR, 'already_logged')
        else:
            agi.set_variable(AGENTSTATUS_VAR, 'error')
    else:
        agi.set_variable(AGENTSTATUS_VAR, 'logged')


def agent_logoff(agi, cursor, args):
    try:
        agent_id = int(args[0])

        _do_agent_logoff(agi, agent_id)
    except Exception as e:
        logger.exception("Error while logging off agent")
        agi.dp_break(e)


def _do_agent_logoff(agi, agent_id):
    agent_client.logoff_agent(agent_id)


def setup_agent(cursor):
    global agent_client
    if agent_client is None:
        agent_client = AgentClient()
        agent_client.connect('localhost')


agid.register(agent_login, setup_agent)
agid.register(agent_logoff, setup_agent)
