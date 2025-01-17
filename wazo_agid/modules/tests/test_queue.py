# Copyright 2013-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import unittest
from unittest.mock import Mock

from wazo_agid import dialplan_variables, fastagi, objects
from wazo_agid.modules import incoming_queue_set_features

QUEUE_WRAPUP_TIME = '__QUEUEWRAPUPTIME'


class TestQueue(unittest.TestCase):
    def setUp(self):
        self.queue = Mock(objects.Queue)
        self.agi = Mock(fastagi.FastAGI)

    def test_set_wrapup_time(self):
        self.queue.wrapuptime = None
        incoming_queue_set_features._set_wrapup_time(self.agi, self.queue)
        self.assert_dialplan_variable_not_set(self.agi, QUEUE_WRAPUP_TIME)

        self.queue.wrapuptime = 0
        incoming_queue_set_features._set_wrapup_time(self.agi, self.queue)
        self.assert_dialplan_variable_not_set(self.agi, QUEUE_WRAPUP_TIME)

        self.queue.wrapuptime = 30
        incoming_queue_set_features._set_wrapup_time(self.agi, self.queue)
        self.assert_dialplan_variable_set(self.agi, QUEUE_WRAPUP_TIME, 30)

    def test_set_call_record_toggle_enabled(self):
        self.queue.dtmf_record_toggle = True
        incoming_queue_set_features._set_call_record_toggle(self.agi, self.queue)
        self.assert_dialplan_variable_set(
            self.agi, f'__{dialplan_variables.QUEUE_DTMF_RECORD_TOGGLE_ENABLED}', '1'
        )

    def test_set_call_record_toggle_disabled(self):
        self.queue.dtmf_record_toggle = False
        incoming_queue_set_features._set_call_record_toggle(self.agi, self.queue)
        self.assert_dialplan_variable_set(
            self.agi, f'__{dialplan_variables.QUEUE_DTMF_RECORD_TOGGLE_ENABLED}', '0'
        )

    def assert_dialplan_variable_not_set(self, agi, unexpected_variable_name):
        value = self.get_channel_variable_value(agi, unexpected_variable_name)
        self.assertIsNone(value)

    def assert_dialplan_variable_set(self, agi, expected_variable_name, expected_value):
        value = self.get_channel_variable_value(agi, expected_variable_name)
        self.assertEqual(value, expected_value)

    def get_channel_variable_value(self, agi, modifier_variable):
        for call in agi.set_variable.call_args_list:
            variable_name, value = call[0]
            if variable_name == modifier_variable:
                return value
        return None
