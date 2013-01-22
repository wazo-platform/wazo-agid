# -*- coding: utf-8 -*-

# Copyright (C) 2013 Avencall
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
from xivo_agid import objects
from xivo_agid import fastagi
from xivo_agid.modules import incoming_queue_set_features

QUEUE_WRAPUP_TIME = '__QUEUEWRAPUPTIME'


class TestQueue(unittest.TestCase):

    def test_set_wrapup_time(self):
        queue = Mock(objects.Queue)
        agi = Mock(fastagi.FastAGI)

        queue.wrapuptime = None
        incoming_queue_set_features._set_wrapup_time(agi, queue)
        self.assert_dialplan_variable_not_set(agi, QUEUE_WRAPUP_TIME)

        queue.wrapuptime = 0
        incoming_queue_set_features._set_wrapup_time(agi, queue)
        self.assert_dialplan_variable_not_set(agi, QUEUE_WRAPUP_TIME)

        queue.wrapuptime = 30
        incoming_queue_set_features._set_wrapup_time(agi, queue)
        self.assert_dialplan_variable_set(agi, QUEUE_WRAPUP_TIME, 30)

    def assert_dialplan_variable_not_set(self, agi, unexpected_variable_name):
        value = self.get_channel_variable_value(agi, unexpected_variable_name)
        self.assertEqual(value, None)

    def assert_dialplan_variable_set(self, agi, expected_variable_name, expected_value):
        value = self.get_channel_variable_value(agi, expected_variable_name)
        self.assertEqual(value, expected_value)

    def get_channel_variable_value(self, agi, modifier_variable):
        for call in agi.set_variable.call_args_list:
            variable_name, value = call[0]
            if variable_name == modifier_variable:
                return value
        return None
