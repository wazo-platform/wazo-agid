# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

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
