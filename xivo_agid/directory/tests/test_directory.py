# -*- coding: utf-8 -*-

# Copyright (C) 2015 Avencall
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

from ..directory import Context

from hamcrest import assert_that, equal_to
from mock import Mock


class TestReverseLookup(unittest.TestCase):

    def test_that_partial_numbers_are_not_matched(self):
        expected_result = {'number': '18005551000',
                           'name': 'Alice'}
        directory_one = Mock(lookup_reverse=Mock(return_value=[{'number': '1000', 'name': 'bob'}]))
        directory_two = Mock(lookup_reverse=Mock(return_value=[expected_result]))
        directories = {'*': [directory_one, directory_two]}

        context = Context(None, None, directories)

        result = context.lookup_reverse('lol', '18005551000')

        assert_that(result, equal_to(expected_result))
