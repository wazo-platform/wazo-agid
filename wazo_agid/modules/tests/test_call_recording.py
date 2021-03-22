# -*- coding: utf-8 -*-
# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import assert_that, equal_to

from ..call_recording import _has_option


class TestHasOption(unittest.TestCase):

    def test_has_option(self):
        option = 'p'
        tests = [
            ('', False),
            ('p', True),
            ('P', False),
            ('abc(p)', False),
            ('a(foo)bc(p)', False),
            ('ab(foo)p', True),
        ]

        for options, expected in tests:
            result = _has_option(options, option)
            assert_that(result, equal_to(expected), options)
