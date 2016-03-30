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
from xivo_agid.modules.phone_set_feature import (_phone_set_busy,
                                                 _phone_set_dnd,
                                                 _phone_set_incallfilter,
                                                 _phone_set_rna,
                                                 _phone_set_unc)


class TestPhoneSetFeature(unittest.TestCase):

    def setUp(self):
        self._user_id = 2
        self._client = Mock().return_value
        self._agi = Mock()
        self._agi.config = {'confd': {'client': self._client}}
        self._agi.get_variable.return_value = self._user_id

    def test_phone_set_dnd(self):
        self._client.users(self._user_id).get_service.return_value = {'enabled': True}

        _phone_set_dnd(self._agi, None, None)

        self._client.users(self._user_id).get_service.assert_called_once_with('dnd')
        self._client.users(self._user_id).update_service.assert_called_once_with('dnd', {'enabled': False})
        expected_calls = [
            call('XIVO_DNDENABLED', False),
            call('XIVO_USERID_OWNER', self._user_id),
        ]
        self._agi.set_variable.assert_has_calls(expected_calls)

    def test_phone_set_incallfilter(self):
        self._client.users(self._user_id).get_service.return_value = {'enabled': False}

        _phone_set_incallfilter(self._agi, None, None)

        self._client.users(self._user_id).get_service.assert_called_once_with('incallfilter')
        self._client.users(self._user_id).update_service.assert_called_once_with('incallfilter', {'enabled': True})
        expected_calls = [
            call('XIVO_INCALLFILTERENABLED', True),
            call('XIVO_USERID_OWNER', self._user_id),
        ]
        self._agi.set_variable.assert_has_calls(expected_calls)

    def test_phone_set_busy(self):
        args = [None, '1', '123']

        _phone_set_busy(self._agi, None, args)

        self._client.users(self._user_id).update_forward.assert_called_once_with('busy', {'enabled': True,
                                                                                          'destination': '123'})
        expected_calls = [
            call('XIVO_USERID_OWNER', self._user_id),
            call('XIVO_BUSYENABLED', 1),
        ]
        self._agi.set_variable.assert_has_calls(expected_calls)

    def test_phone_set_busy_do_not_set_variable_when_raise_exception(self):
        args = [None, '1', '123']
        self._client.users(self._user_id).update_forward.side_effect = Exception()

        _phone_set_busy(self._agi, None, args)

        self._agi.set_variable.assert_not_called()

    def test_phone_set_rna(self):
        args = [None, '0', '123']

        _phone_set_rna(self._agi, None, args)

        self._client.users(self._user_id).update_forward.assert_called_once_with('noanswer', {'enabled': False,
                                                                                              'destination': '123'})
        expected_calls = [
            call('XIVO_USERID_OWNER', self._user_id),
            call('XIVO_RNAENABLED', 0),
        ]
        self._agi.set_variable.assert_has_calls(expected_calls)

    def test_phone_set_rna_do_not_set_variable_when_raise_exception(self):
        args = [None, '1', '123']
        self._client.users(self._user_id).update_forward.side_effect = Exception()

        _phone_set_rna(self._agi, None, args)

        self._agi.set_variable.assert_not_called()

    def test_phone_set_unc(self):
        args = [None, '1', '123']

        _phone_set_unc(self._agi, None, args)

        self._client.users(self._user_id).update_forward.assert_called_once_with(
            'unconditional', {'enabled': True,
                              'destination': '123'})
        expected_calls = [
            call('XIVO_USERID_OWNER', self._user_id),
            call('XIVO_UNCENABLED', 1),
        ]
        self._agi.set_variable.assert_has_calls(expected_calls)

    def test_phone_set_unc_do_not_set_variable_when_raise_exception(self):
        args = [None, '1', '123']
        self._client.users(self._user_id).update_forward.side_effect = Exception()

        _phone_set_unc(self._agi, None, args)

        self._agi.set_variable.assert_not_called()
