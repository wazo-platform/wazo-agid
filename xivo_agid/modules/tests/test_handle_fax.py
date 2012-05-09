# -*- coding: UTF-8 -*-

import unittest
from xivo_agid.modules.handle_fax import _convert_config_value_to_bool


class TestConvertConfigValue(unittest.TestCase):
    def setUp(self):
        self._default = object()

    def assertIsDefault(self, value):
        self.assertTrue(value is self._default)

    def _convert_to_bool(self, config_value):
        return _convert_config_value_to_bool(config_value, self._default, 'test')

    def test_with_none_value(self):
        bool_value = self._convert_to_bool(None)

        self.assertIsDefault(bool_value)

    def test_with_0_value(self):
        bool_value = self._convert_to_bool('0')

        self.assertEqual(False, bool_value)

    def test_with_1_value(self):
        bool_value = self._convert_to_bool('1')

        self.assertEqual(True, bool_value)

    def test_with_invalid_value(self):
        bool_value = self._convert_to_bool('2')

        self.assertIsDefault(bool_value)
