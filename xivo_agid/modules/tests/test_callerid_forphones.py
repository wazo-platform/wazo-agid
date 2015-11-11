# -*- coding: utf-8 -*-

# Copyright (C) 2013-2015 Avencall
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

    @patch('xivo_agid.modules.callerid_forphones.DirdClient')
    def test_callerid_forphones_no_lookup(self, mock_DirdClient):
        mock_agi = Mock(FastAGI)
        mock_agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        mock_agi.config = {'dird': {'host': 'localhost',
                                    'port': 9489,
                                    'timeout': 1},
                           'token': 'valid-token'}

        callerid_forphones(mock_agi, Mock(), Mock())

        mock_dird_client = Mock()
        mock_DirdClient.return_value = mock_dird_client
        assert_that(mock_dird_client.directories.reverse.call_count, equal_to(0))

    @patch('xivo_agid.modules.callerid_forphones.DirdClient')
    @patch('xivo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_no_result(self, mock_dao, mock_DirdClient):
        mock_agi = Mock(FastAGI)
        mock_agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        mock_agi.config = {'dird': {'host': 'localhost',
                                    'port': 9489,
                                    'timeout': 1},
                           'token': 'valid-token'}

        mock_dird_client = Mock()
        mock_DirdClient.return_value = mock_dird_client
        mock_dird_client.directories.reverse.return_value = {'display': None}
        mock_dao.find_by_incall_id.return_value = ['xivo_user_uuid', 'profile']

        callerid_forphones(mock_agi, Mock(), Mock())

        assert_that(mock_dird_client.directories.reverse.call_count, equal_to(1))

        assert_that(mock_agi.set_callerid.call_count, equal_to(0))

    @patch('xivo_agid.modules.callerid_forphones.DirdClient')
    @patch('xivo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_with_result(self, mock_dao, mock_DirdClient):
        mock_agi = Mock(FastAGI)
        mock_agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        mock_agi.config = {'dird': {'host': 'localhost',
                                    'port': 9489,
                                    'timeout': 1},
                           'token': 'valid-token'}

        mock_dird_client = Mock()
        mock_DirdClient.return_value = mock_dird_client
        lookup_result = {'number': '415', 'firstname': 'Bob', 'lastname': 'wonderland'}
        mock_dird_client.directories.reverse.return_value = {'display': 'Bob',
                                                             'fields': lookup_result}
        mock_dao.find_by_incall_id.return_value = ['xivo_user_uuid', 'profile']

        callerid_forphones(mock_agi, Mock(), Mock())

        expected_callerid = '"Bob" <5555551234>'
        mock_agi.set_callerid.assert_called_once_with(expected_callerid)
        _, set_var_result = mock_agi.set_variable.call_args[0]
        for key, value in lookup_result.iteritems():
            s = '%s: %s' % (key, value)
            assert_that(set_var_result, contains_string(s))

    @patch('xivo_agid.modules.callerid_forphones.DirdClient')
    def test_that_callerid_forphones_never_raises(self, mock_DirdClient):
        mock_agi = Mock(FastAGI)
        mock_agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        mock_agi.config = {'dird': {'host': 'localhost',
                                    'port': 9489,
                                    'timeout': 1},
                           'token': 'valid-token'}
        mock_dird_client = Mock()
        mock_DirdClient.return_value = mock_dird_client
        mock_dird_client.directories.reverse.side_effect = AssertionError('Should not raise')

        callerid_forphones(mock_agi, Mock(), Mock())
