# -*- coding: utf-8 -*-
# Copyright 2017-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from hamcrest import assert_that, equal_to, greater_than

from ..helpers import CallRecordingNameGenerator


class TestCallRecordingNameGenerator(unittest.TestCase):

    def test_that_unicode_chars_are_replaced(self):
        generator = CallRecordingNameGenerator(u'{{ name }}', 'wav')

        result = generator.generate({'name': u'pépé'})

        assert_that(result, equal_to('pepe.wav'))

    def test_that_unacceptable_chars_are_removed(self):
        generator = CallRecordingNameGenerator(u'{{ name }}', 'wav')

        result = generator.generate({'name': u'test\**test'})

        assert_that(result, equal_to('testtest.wav'))

    def test_that_empty_names_are_not_generated(self):
        generator = CallRecordingNameGenerator(u'{{ name }}', 'wav')

        result = generator.generate({'name': u'\**'})

        name, extension = result.rsplit('.', 1)
        assert_that(len(name), greater_than(0), 'a name should have been generated')
        assert_that(extension, equal_to('wav'))
