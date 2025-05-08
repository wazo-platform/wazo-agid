# Copyright 2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import unittest

import phonenumbers

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
