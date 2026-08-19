# Copyright 2025-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import phonenumbers
import requests

from wazo_agid.fastagi import FastAGI
from wazo_agid.modules import screen_blocklist


class TestInterpretNumber(unittest.TestCase):
    def test_e164_number(self):
        raw_number = '+18001235555'
        for country in ('US', 'FR', 'CA', 'GB'):
            with self.subTest(country=country):
                number = screen_blocklist.interpret_number(raw_number, country)
                self.assertEqual(number.country_code, 1)
                self.assertEqual(number.national_number, 8001235555)

    def test_invalid_number(self):
        with self.assertRaises(phonenumbers.NumberParseException):
            screen_blocklist.interpret_number('invalid', 'US')

    def test_european_number_dialling_prefix(self):
        raw_number = '0033123456789'
        for country in ('FR', 'DE', 'ES', 'IT', None):
            with self.subTest(country=country):
                number = screen_blocklist.interpret_number(raw_number, country)
                self.assertEqual(number.country_code, 33)
                self.assertEqual(number.national_number, 123456789)

    def test_nanpa_number_dialling_prefix(self):
        raw_number = '01118001235555'
        for country in ('US', 'CA'):
            with self.subTest(country=country):
                number = screen_blocklist.interpret_number(raw_number, country)
                self.assertEqual(number.country_code, 1)
                self.assertEqual(number.national_number, 8001235555)


class TestScreenBlocklist(unittest.TestCase):
    def setUp(self):
        self.confd_client = Mock()
        self.lookup = self.confd_client.users.return_value.blocklist.numbers.lookup

        self.agi = Mock(FastAGI)
        self.agi.config = {'confd': {'client': self.confd_client}}
        self.agi.get_variable.return_value = '+18001235555'

        user_dao_patch = patch.object(screen_blocklist, 'user_dao')
        self.user_dao = user_dao_patch.start()
        self.addCleanup(user_dao_patch.stop)
        self.user_dao.get_by.return_value = Mock(
            country='US', tenant_uuid='tenant-uuid'
        )

    def test_blocked_number_sets_variable(self):
        self.lookup.return_value = 'blocklist-number-uuid'

        screen_blocklist.screen_blocklist(self.agi, Mock(), ['user-uuid'])

        self.agi.set_variable.assert_called_once_with(
            'WAZO_BLOCKED_NUMBER_UUID', 'blocklist-number-uuid'
        )

    def test_number_not_blocked_leaves_variable_unset(self):
        self.lookup.return_value = None

        screen_blocklist.screen_blocklist(self.agi, Mock(), ['user-uuid'])

        self.agi.set_variable.assert_not_called()

    def test_http_error_lets_the_call_through(self):
        self.lookup.side_effect = requests.exceptions.HTTPError('401 Unauthorized')

        screen_blocklist.screen_blocklist(self.agi, Mock(), ['user-uuid'])

        self.agi.set_variable.assert_not_called()

    def test_connection_error_lets_the_call_through(self):
        self.lookup.side_effect = requests.exceptions.ConnectionError(
            'Connection refused'
        )

        screen_blocklist.screen_blocklist(self.agi, Mock(), ['user-uuid'])

        self.agi.set_variable.assert_not_called()
