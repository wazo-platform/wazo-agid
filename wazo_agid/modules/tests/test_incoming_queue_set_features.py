# -*- coding: utf-8 -*-
# Copyright (C) 2015 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from mock import Mock, patch
from xivo_agid.modules import incoming_queue_set_features


class TestHoldtimeAnnounce(unittest.TestCase):

    def setUp(self):
        self.agi = Mock()
        self.cursor = Mock()
        self.args = []
        self.queue = Mock()
        self.queue.announce_holdtime = 1

    @patch('xivo_agid.objects.Queue')
    def test_holdtime_use_say_number(self, mock_Queue):
        holdtime_minute = 24
        holdtime_second = holdtime_minute * 60
        self.agi.get_variable.return_value = holdtime_second
        mock_Queue.return_value = self.queue

        incoming_queue_set_features.holdtime_announce(self.agi, self.cursor, self.args)

        self.agi.say_number.assert_called_once_with(str(holdtime_minute), gender='')

    @patch('xivo_agid.objects.Queue')
    def test_holdtime_use_gender_number(self, mock_Queue):
        holdtime_minute = 1
        holdtime_second = holdtime_minute * 60
        self.agi.get_variable.return_value = holdtime_second
        mock_Queue.return_value = self.queue

        incoming_queue_set_features.holdtime_announce(self.agi, self.cursor, self.args)

        self.agi.say_number.assert_called_once_with(str(holdtime_minute), gender='f')
