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

        self.agi.say_number.assert_called_once_with(str(holdtime_minute))
