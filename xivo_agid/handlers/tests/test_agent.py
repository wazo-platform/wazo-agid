# -*- coding: utf-8 -*-

# Copyright (C) 2015 Avencall
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

import unittest

from mock import ANY, Mock, patch
from xivo_agentd_client import error
from xivo_agentd_client.error import AgentdClientError
from xivo_agid.fastagi import FastAGI
from xivo_agid.handlers import agent


@patch('xivo_agid.handlers.agent.AgentdClient')
class TestAgent(unittest.TestCase):

    def setUp(self):
        self.agentd_config = {'foo': 'bar'}
        self.token_id = 'some-token-id'
        self.agi = Mock(FastAGI)
        self.agi.config = {
            'agentd': self.agentd_config,
            'auth': {'token': self.token_id},
        }
        self.agentd_client = Mock()
        self.agent_id = 11
        self.extension = '1234'
        self.context = 'foobar'

    def test_login_agent(self, AgentdClient):
        AgentdClient.return_value = self.agentd_client

        agent.login_agent(self.agi, self.agent_id, self.extension, self.context)

        AgentdClient.assert_called_once_with(token=self.token_id, **self.agentd_config)
        self.agentd_client.agents.login_agent.assert_called_once_with(self.agent_id,
                                                                      self.extension,
                                                                      self.context)
        self.agi.set_variable.assert_called_once_with(agent.AGENTSTATUS_VAR, 'logged')

    def test_login_agent_on_already_logged(self, AgentdClient):
        AgentdClient.return_value = self.agentd_client
        self.agentd_client.agents.login_agent.side_effect = AgentdClientError(error.ALREADY_LOGGED)

        agent.login_agent(self.agi, self.agent_id, self.extension, self.context)

        self.agi.set_variable.assert_called_once_with(agent.AGENTSTATUS_VAR, 'already_logged')

    def test_login_agent_on_already_in_use(self, AgentdClient):
        AgentdClient.return_value = self.agentd_client
        self.agentd_client.agents.login_agent.side_effect = AgentdClientError(error.ALREADY_IN_USE)

        agent.login_agent(self.agi, self.agent_id, self.extension, self.context)

        self.agi.set_variable.assert_called_once_with(agent.AGENTSTATUS_VAR, 'already_in_use')

    def test_login_agent_on_other_error(self, AgentdClient):
        AgentdClient.return_value = self.agentd_client
        self.agentd_client.agents.login_agent.side_effect = AgentdClientError('foobar')

        self.assertRaises(AgentdClientError, agent.login_agent, self.agi, self.agent_id, self.extension, self.context)

    def test_logoff_agent(self, AgentdClient):
        AgentdClient.return_value = self.agentd_client

        agent.logoff_agent(self.agi, self.agent_id)

        AgentdClient.assert_called_once_with(token=self.token_id, **self.agentd_config)
        self.agentd_client.agents.logoff_agent.assert_called_once_with(self.agent_id)

    def test_logoff_agent_on_not_logged(self, AgentdClient):
        AgentdClient.return_value = self.agentd_client
        self.agentd_client.agents.logoff_agent.side_effect = AgentdClientError(error.NOT_LOGGED)

        agent.logoff_agent(self.agi, self.agent_id)

    def test_logoff_agent_on_other_error(self, AgentdClient):
        AgentdClient.return_value = self.agentd_client
        self.agentd_client.agents.logoff_agent.side_effect = AgentdClientError('foobar')

        self.assertRaises(AgentdClientError, agent.logoff_agent, self.agi, self.agent_id)

    def test_get_agent_status(self, AgentdClient):
        AgentdClient.return_value = self.agentd_client

        agent.get_agent_status(self.agi, self.agent_id)

        AgentdClient.assert_called_once_with(token=self.token_id, **self.agentd_config)
        self.agentd_client.agents.get_agent_status.assert_called_once_with(self.agent_id)
        self.agi.set_variable.assert_called_once_with('XIVO_AGENT_LOGIN_STATUS', ANY)
