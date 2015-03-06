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
from hamcrest import assert_that, equal_to
from mock import ANY, Mock, call, patch
from xivo_agid.modules import check_diversion


class TestCheckDiversion(unittest.TestCase):

    def setUp(self):
        self.agi = Mock()
        self.cursor = Mock()
        self.queue = Mock(name='foo')

    def test_is_agent_ratio_overrun_no_waiting_calls(self):
        self.queue.waitratio = 1.0
        waiting_calls = 0

        self.assertFalse(check_diversion._is_agent_ratio_overrun(self.agi, self.queue, waiting_calls))

    def test_is_agent_ratio_overrun_0_members(self):
        self.queue.waitratio = 1.0
        self.agi.get_variable.return_value = '0'
        waiting_calls = 2

        self.assertTrue(check_diversion._is_agent_ratio_overrun(self.agi, self.queue, waiting_calls))
        self.agi.get_variable.assert_called_once_with('QUEUE_MEMBER({},logged)'.format(self.queue.name))

    def test_is_agent_ratio_overrun_over(self):
        self.queue.waitratio = 0.70
        self.agi.get_variable.return_value = '4'
        waiting_calls = 2

        self.assertTrue(check_diversion._is_agent_ratio_overrun(self.agi, self.queue, waiting_calls))

    def test_is_agent_ratio_overrun_under(self):
        self.queue.waitratio = 0.80
        self.agi.get_variable.return_value = '4'
        waiting_calls = 2

        self.assertFalse(check_diversion._is_agent_ratio_overrun(self.agi, self.queue, waiting_calls))

    @patch('xivo_agid.modules.check_diversion.objects')
    def test_check_diversion_xivo_divert_event_is_cleared(self, mock_objects):
        self.queue.waittime = None
        self.queue.waitratio = None
        self.agi.get_variable.return_value = 42

        check_diversion.check_diversion(self.agi, self.cursor, None)

        expected = [
            call('XIVO_DIVERT_EVENT', ''),
            call('XIVO_FWD_TYPE', ANY)
        ]
        assert_that(self.agi.set_variable.call_args_list, equal_to(expected))
