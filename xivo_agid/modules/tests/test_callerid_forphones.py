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


@patch('xivo_agid.modules.callerid_forphones.DirdClient')
class TestCallerIdForPhone(unittest.TestCase):

    def setUp(self):
        self.agi = Mock(FastAGI)
        self.agi.config = {
            'dird': {'host': 'localhost',
                     'port': 9489,
                     'timeout': 1,
                     'verify_certificate': False},
            'auth': {'token': 'valid-token'}
        }
        self.agi.get_variable.return_value = '42'

    def test_callerid_forphones_no_lookup(self, mock_DirdClient):
        self.agi.env = {
            'agi_calleridname': 'Alice',
            'agi_callerid': '5555551234',
        }
        dird_client = Mock()
        mock_DirdClient.return_value = dird_client
        dird_client.directories.reverse.return_value = {'display': None}

        callerid_forphones(self.agi, Mock(), Mock())

        assert_that(dird_client.directories.reverse.call_count, equal_to(0))

    @patch('xivo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_no_result(self, mock_dao, mock_DirdClient):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        dird_client = Mock()
        mock_DirdClient.return_value = dird_client
        dird_client.directories.reverse.return_value = {'display': None}
        dao_result = Mock()
        mock_dao.find_by_incall_id.return_value = dao_result
        dao_result.xivo_user_uuid = 'xivo_user_uuid'

        callerid_forphones(self.agi, Mock(), Mock())

        assert_that(dird_client.directories.reverse.call_count, equal_to(1))
        assert_that(self.agi.set_callerid.call_count, equal_to(0))

    @patch('xivo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_with_result(self, mock_dao, mock_DirdClient):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }

        mock_dird_client = Mock()
        mock_DirdClient.return_value = mock_dird_client
        lookup_result = {'number': '415', 'firstname': 'Bob', 'lastname': 'wonderland'}
        mock_dird_client.directories.reverse.return_value = {'display': 'Bob',
                                                             'fields': lookup_result}
        dao_result = Mock()
        mock_dao.find_by_incall_id.return_value = dao_result
        dao_result.xivo_user_uuid = 'xivo_user_uuid'

        callerid_forphones(self.agi, Mock(), Mock())

        expected_callerid = '"Bob" <5555551234>'
        self.agi.set_callerid.assert_called_once_with(expected_callerid)
        _, set_var_result = self.agi.set_variable.call_args[0]
        for key, value in lookup_result.iteritems():
            s = '%s: %s' % (key, value)
            assert_that(set_var_result, contains_string(s))

    @patch('xivo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_when_dao_return_none(self, mock_dao, mock_DirdClient):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        dird_client = Mock()
        mock_DirdClient.return_value = dird_client
        dird_client.directories.reverse.return_value = {'display': None}
        mock_dao.find_by_incall_id.return_value = None

        callerid_forphones(self.agi, Mock(), Mock())

        assert_that(dird_client.directories.reverse.call_count, equal_to(1))
        assert_that(self.agi.set_callerid.call_count, equal_to(0))

    def test_that_callerid_forphones_never_raises(self, mock_DirdClient):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        mock_dird_client = Mock()
        mock_DirdClient.return_value = mock_dird_client
        mock_dird_client.directories.reverse.side_effect = AssertionError('Should not raise')

        callerid_forphones(self.agi, Mock(), Mock())
