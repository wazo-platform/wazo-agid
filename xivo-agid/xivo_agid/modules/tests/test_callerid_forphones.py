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

import unittest

from hamcrest import assert_that
from hamcrest import contains_string
from hamcrest import equal_to
from mock import Mock
from mock import patch
from xivo_agid.fastagi import FastAGI
from xivo_agid.modules.callerid_forphones import callerid_forphones


class TestCallerIdForPhone(unittest.TestCase):

    @patch('xivo_agid.modules.callerid_forphones._reverse_lookup')
    def test_callerid_forphones_no_lookup(self, mock_reverse_lookup):
        mock_agi = Mock(FastAGI)
        mock_agi.env = {
            'agi_calleridname': 'Pierre',
            'agi_callerid': '5555551234',
        }

        callerid_forphones(mock_agi, Mock(), Mock())

        assert_that(mock_reverse_lookup.call_count, equal_to(0),
                    '_reverse_lookup call count')

    @patch('xivo_agid.modules.callerid_forphones._reverse_lookup')
    def test_callerid_forphones_no_result(self, mock_reverse_lookup):
        mock_agi = Mock(FastAGI)
        mock_agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        mock_reverse_lookup.return_value = {}

        callerid_forphones(mock_agi, Mock(), Mock())

        assert_that(mock_reverse_lookup.call_count, equal_to(1),
                    '_reverse_lookup call count')
        assert_that(mock_agi.set_callerid.call_count, equal_to(0),
                    'set_callerid call count')
        mock_agi.set_variable.assert_called_once_with('XIVO_REVERSE_LOOKUP', '')

    @patch('xivo_agid.modules.callerid_forphones._reverse_lookup')
    def test_callerid_forphones_with_result(self, mock_reverse_lookup):
        mock_agi = Mock(FastAGI)
        mock_agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        mock_reverse_lookup.return_value = lookup_result = {
            'db-reverse': 'Pierre',
            'db-mail': 'pierre@home.com',
            'db-fullanme': 'Pierre LaRoche',
        }

        callerid_forphones(mock_agi, Mock(), Mock())

        expected_callerid = '"Pierre" <5555551234>'
        mock_agi.set_callerid.assert_called_once_with(expected_callerid)
        _, set_var_result = mock_agi.set_variable.call_args[0]
        for key, value in lookup_result.iteritems():
            s = '%s: %s' % (key, value)
            assert_that(set_var_result, contains_string(s))
