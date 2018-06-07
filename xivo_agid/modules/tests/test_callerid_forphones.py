# -*- coding: utf-8 -*-
# Copyright (C) 2013-2016 Avencall
# SPDX-License-Identifier: GPL-3.0+

import unittest

from hamcrest import assert_that
from hamcrest import contains_string
from hamcrest import equal_to
from mock import Mock
from mock import patch
from xivo_agid.fastagi import FastAGI
from xivo_agid.modules.callerid_forphones import callerid_forphones


class TestCallerIdForPhone(unittest.TestCase):

    def setUp(self):
        self.agi = Mock(FastAGI)
        self.dird_client = Mock()
        self.agi.config = {'dird': {'client': self.dird_client}}
        self.agi.get_variable.return_value = '42'

    def test_callerid_forphones_no_lookup(self):
        self.agi.env = {
            'agi_calleridname': 'Alice',
            'agi_callerid': '5555551234',
        }
        self.dird_client.directories.reverse.return_value = {'display': None}

        callerid_forphones(self.agi, Mock(), Mock())

        assert_that(self.dird_client.directories.reverse.call_count, equal_to(0))

    @patch('xivo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_no_result(self, mock_dao):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        self.dird_client.directories.reverse.return_value = {'display': None}
        mock_dao.find_by_incall_id.return_value.xivo_user_uuid = 'xivo_user_uuid'

        callerid_forphones(self.agi, Mock(), Mock())

        assert_that(self.dird_client.directories.reverse.call_count, equal_to(1))
        assert_that(self.agi.set_callerid.call_count, equal_to(0))

    @patch('xivo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_with_result(self, mock_dao):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }

        lookup_result = {'number': '415', 'firstname': 'Bob', 'lastname': 'wonderland'}
        self.dird_client.directories.reverse.return_value = {'display': 'Bob',
                                                             'fields': lookup_result}
        mock_dao.find_by_incall_id.return_value.xivo_user_uuid = 'xivo_user_uuid'

        callerid_forphones(self.agi, Mock(), Mock())

        expected_callerid = '"Bob" <5555551234>'
        self.agi.set_callerid.assert_called_once_with(expected_callerid)
        _, set_var_result = self.agi.set_variable.call_args[0]
        for key, value in lookup_result.iteritems():
            s = '%s: %s' % (key, value)
            assert_that(set_var_result, contains_string(s))

    @patch('xivo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_when_dao_return_none(self, mock_dao):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        self.dird_client.directories.reverse.return_value = {'display': None}
        mock_dao.find_by_incall_id.return_value = None

        callerid_forphones(self.agi, Mock(), Mock())

        assert_that(self.dird_client.directories.reverse.call_count, equal_to(1))
        assert_that(self.agi.set_callerid.call_count, equal_to(0))

    def test_that_callerid_forphones_never_raises(self):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        self.dird_client.directories.reverse.side_effect = AssertionError('Should not raise')

        callerid_forphones(self.agi, Mock(), Mock())
