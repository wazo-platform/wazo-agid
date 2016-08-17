# -*- coding: utf-8 -*-

# Copyright (C) 2013-2016 Avencall
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

from mock import patch, sentinel
from hamcrest import assert_that, equal_to

from xivo_agid.modules.handle_fax import _convert_config_value_to_bool, _build_backends_list


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


class TestBuildBackendList(unittest.TestCase):

    def setUp(self):
        self.available_backends = {'foo': sentinel.foo_backend,
                                   'bar': sentinel.bar_backend}

    def test_build_backends_list(self):
        backend_ids = ['foo']

        backends = _build_backends_list(self.available_backends, backend_ids, '')

        assert_that(backends, equal_to([sentinel.foo_backend]))

    @patch('xivo_agid.modules.handle_fax.logger')
    def test_build_backends_list_referencing_unknown_backend(self, mock_logger):
        backend_ids = ['foo', 'potato']

        backends = _build_backends_list(self.available_backends, backend_ids, '')

        assert_that(backends, equal_to([sentinel.foo_backend]))
        assert_that(mock_logger.warning.call_count, equal_to(1))
