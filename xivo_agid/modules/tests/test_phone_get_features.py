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

from mock import call, Mock
from xivo_agid.modules.phone_get_features import _set_current_forwards


class TestGetFeatures(unittest.TestCase):

    def setUp(self):
        self._user_id = 2
        self._client = Mock().return_value
        self._agi = Mock()
        self._agi.config = {'confd': {'client': self._client}}
        self._agi.get_variable.return_value = self._user_id

    def test_set_current_forwards_variables(self):
        self._client.users(self._user_id).list_forwards.return_value = {
            'busy': {'enabled': True, 'destination': '1234'},
            'noanswer': {'enabled': False, 'destination': '5678'},
            'unconditional': {'enabled': False, 'destination': None}}

        _set_current_forwards(self._agi, self._user_id)

        self._client.users(self._user_id).list_forwards.assert_called_once_with()
        expected_calls = [
            call('XIVO_ENABLEBUSY', 1),
            call('XIVO_DESTBUSY', '1234'),
            call('XIVO_ENABLERNA', 0),
            call('XIVO_DESTRNA', '5678'),
            call('XIVO_ENABLEUNC', 0),
            call('XIVO_DESTUNC', ''),
        ]
        self._agi.set_variable.assert_has_calls(expected_calls)

    def test_set_current_forwards_set_default_variables_on_error(self):
        self._client.users(self._user_id).list_forwards.side_effect = Exception()

        _set_current_forwards(self._agi, self._user_id)

        expected_calls = [
            call('XIVO_ENABLEBUSY', 0),
            call('XIVO_DESTBUSY', ''),
            call('XIVO_ENABLERNA', 0),
            call('XIVO_DESTRNA', ''),
            call('XIVO_ENABLEUNC', 0),
            call('XIVO_DESTUNC', ''),
        ]
        self._agi.set_variable.assert_has_calls(expected_calls)
