# Copyright 2013-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from unittest import TestCase
from unittest.mock import Mock

from wazo_agid.agid import Handler


class TestHandler(TestCase):
    def test_handler_setup_calls_setup_function(self):
        setup_function = Mock()
        fake_cursor = object()

        handler = Handler("foo", setup_function, Mock())
        handler.setup(fake_cursor)

        setup_function.assert_called_once_with(fake_cursor)
