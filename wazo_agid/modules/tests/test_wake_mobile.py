# -*- coding: utf-8 -*-
# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest import TestCase

from mock import (
    Mock,
    patch,
    sentinel as s,
)

from ..wake_mobile import wait_for_registration


class TestWaitForRegistration(TestCase):

    def setUp(self):
        self.agi = Mock()
        self.channel_variables = {}
        self.agi.get_variable.side_effect = lambda key: self.channel_variables.get(key, '')


    @patch('wazo_agid.modules.wake_mobile._wait_for_registration')
    def test_timeout_default_value(self, _wait_for_registration):
        default_timeout = 30

        wait_for_registration(self.agi, s.cursor, [s.aor])

        _wait_for_registration.assert_called_once_with(self.agi, s.aor, default_timeout)

    @patch('wazo_agid.modules.wake_mobile._wait_for_registration')
    def test_configured_timeout(self, _wait_for_registration):
        aor = 'foobar'
        timeout = 20
        self.channel_variables['PJSIP_ENDPOINT(foobar,@wake_mobile_timeout)'] = timeout

        wait_for_registration(self.agi, s.cursor, [aor])

        _wait_for_registration.assert_called_once_with(self.agi, aor, timeout)
