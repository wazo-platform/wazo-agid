# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

from unittest.mock import patch, sentinel
from hamcrest import assert_that, equal_to

from wazo_agid.modules.handle_fax import (
    _convert_config_value_to_bool,
    _build_backends_list,
)


class TestConvertConfigValue(unittest.TestCase):
    def setUp(self):
        self._default = object()

    def assertIsDefault(self, value):
        self.assertTrue(value is self._default)

    def _convert_to_bool(self, config_value):
        return _convert_config_value_to_bool(config_value, self._default, 'test')  # type: ignore

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


class TestBuildBackendList(unittest.TestCase):
    def setUp(self):
        self.available_backends = {
            'foo': sentinel.foo_backend,
            'bar': sentinel.bar_backend,
        }

    def test_build_backends_list(self):
        backend_ids = ['foo']

        backends = _build_backends_list(self.available_backends, backend_ids, '')

        assert_that(backends, equal_to([sentinel.foo_backend]))

    @patch('wazo_agid.modules.handle_fax.logger')
    def test_build_backends_list_referencing_unknown_backend(self, mock_logger):
        backend_ids = ['foo', 'potato']

        backends = _build_backends_list(self.available_backends, backend_ids, '')

        assert_that(backends, equal_to([sentinel.foo_backend]))
        assert_that(mock_logger.warning.call_count, equal_to(1))
