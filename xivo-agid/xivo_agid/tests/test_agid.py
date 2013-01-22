# -*- coding: utf-8 -*-

# Copyright (C) 2013 Avencall
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

import mock
import unittest
from xivo_agid.agid import Handler


class TestHandler(unittest.TestCase):
    def test_handler_setup_calls_setup_function(self):
        setup_function = mock.Mock()
        fake_cursor = object()

        handler = Handler("foo", setup_function, mock.Mock())
        handler.setup(fake_cursor)

        setup_function.assert_called_once_with(fake_cursor)
