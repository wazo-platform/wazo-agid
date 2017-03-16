# -*- coding: utf-8 -*-

# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
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

