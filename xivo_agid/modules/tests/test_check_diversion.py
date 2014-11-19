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

import unittest
from mock import Mock
from xivo_agid.modules import check_diversion


class TestCheckDiversion(unittest.TestCase):

    def setUp(self):
        self.agi = Mock()
        self.queue = Mock(name='foo')

    def test_is_agent_ratio_overrun_0_members(self):
        self.queue.waitratio = 70
        self.agi.get_variable.return_value = '0'
        waiting_calls = 2

        self.assertTrue(check_diversion._is_agent_ratio_overrun(self.agi, self.queue, waiting_calls))
        self.agi.get_variable.assert_called_once_with('QUEUE_MEMBER({},logged)'.format(self.queue.name))

    def test_is_agent_ratio_overrun_over(self):
        self.queue.waitratio = 70
        self.agi.get_variable.return_value = '4'
        waiting_calls = 2

        self.assertTrue(check_diversion._is_agent_ratio_overrun(self.agi, self.queue, waiting_calls))

    def test_is_agent_ratio_overrun_under(self):
        self.queue.waitratio = 80
        self.agi.get_variable.return_value = '4'
        waiting_calls = 2

        self.assertFalse(check_diversion._is_agent_ratio_overrun(self.agi, self.queue, waiting_calls))
