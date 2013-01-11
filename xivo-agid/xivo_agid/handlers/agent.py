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

from xivo_agent.ctl import error
from xivo_agent.ctl.client import AgentClient
from xivo_agent.exception import AgentClientError

AGENTSTATUS_VAR = 'XIVO_AGENTSTATUS'

_agent_client = None


def _init_agent_client():
    global _agent_client
    _agent_client = AgentClient()
    _agent_client.connect('localhost')


def _setup_client(fun):
    def aux(*args, **kwargs):
        if _agent_client is None:
            _init_agent_client()
        return fun(*args, **kwargs)
    return aux


@_setup_client
def login_agent(agi, agent_id, extension, context):
    try:
        _agent_client.login_agent(agent_id, extension, context)
    except AgentClientError as e:
        if e.error == error.ALREADY_LOGGED:
            agi.set_variable(AGENTSTATUS_VAR, 'already_logged')
        elif e.error == error.ALREADY_IN_USE:
            agi.set_variable(AGENTSTATUS_VAR, 'already_in_use')
        else:
            raise
    else:
        agi.set_variable(AGENTSTATUS_VAR, 'logged')


@_setup_client
def logoff_agent(agi, agent_id):
    try:
        _agent_client.logoff_agent(agent_id)
    except AgentClientError as e:
        if e.error != error.NOT_LOGGED:
            raise


@_setup_client
def get_agent_status(agi, agent_id):
    status = _agent_client.get_agent_status(agent_id)
    login_status = 'logged_in' if status.logged else 'logged_out'
    agi.set_variable('XIVO_AGENT_LOGIN_STATUS', login_status)
    

@_setup_client
def get_agent_device(agi, agent_id, cursor):
    cursor.query('SELECT state_interface FROM agent_login_status WHERE agent_id = %s',
                 parameters=(agent_id,))
    res = cursor.fetchone()
    if not res:
        raise LookupError("Unable to find agent (id: %s)" % (agent_id))
    device = res[0]
    return device