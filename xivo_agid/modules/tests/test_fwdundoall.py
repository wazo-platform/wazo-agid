# -*- coding: utf-8 -*-

# Copyright (C) 2016 Avencall
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
from xivo_agid.modules.fwdundoall import fwdundoall


class TestFwdUndoAll(unittest.TestCase):

    def test_that_fwdundoall_call_confd(self):
        self._client = Mock().return_value
        user_id = 2
        agi = Mock()
        agi.get_variable.return_value = user_id
        agi.config = {'confd': {'client': self._client}}

        fwdundoall(agi, None, None)

        no_forward = {'enabled': False,
                      'destination': None}
        expected_body = {'busy': no_forward,
                         'noanswer': no_forward,
                         'unconditional': no_forward}

        self._client.users(user_id).update_forwards.assert_called_once_with(expected_body)
