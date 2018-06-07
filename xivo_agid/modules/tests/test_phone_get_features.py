# -*- coding: utf-8 -*-
# Copyright (C) 2016 Avencall
# SPDX-License-Identifier: GPL-3.0+

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
