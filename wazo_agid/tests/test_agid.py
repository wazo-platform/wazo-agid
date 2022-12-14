# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

import mock

from wazo_agid.agid import Handler


class TestHandler(unittest.TestCase):
    def test_handler_setup_calls_setup_function(self):
        setup_function = mock.Mock()
        fake_cursor = object()

        handler = Handler("foo", setup_function, mock.Mock())
        handler.setup(fake_cursor)

        setup_function.assert_called_once_with(fake_cursor)
