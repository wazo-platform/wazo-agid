# -*- coding: utf-8 -*-
# Copyright 2013-2020 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import assert_that
from hamcrest import contains_string
from hamcrest import equal_to
from mock import Mock
from mock import patch
from mock import sentinel
from wazo_agid.fastagi import FastAGI
from wazo_agid.modules.callerid_forphones import callerid_forphones, FAKE_XIVO_USER_UUID


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

    @patch('wazo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_no_result(self, mock_dao):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        self.dird_client.directories.reverse.return_value = {'display': None}
        mock_dao.find_by_incall_id.return_value.xivo_user_uuid = 'user_uuid'

        self.agi.get_variable.side_effect = [0, sentinel.agi_variable]

        callerid_forphones(self.agi, Mock(), Mock())

        self.dird_client.directories.reverse.assert_called_once_with(
            profile='default',
            user_uuid='user_uuid',
            exten=self.agi.env['agi_callerid'],
            tenant_uuid=sentinel.agi_variable,
        )

        assert_that(self.agi.set_callerid.call_count, equal_to(0))

    @patch('wazo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_with_result(self, mock_dao):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }

        lookup_result = {'number': '415', 'firstname': 'Bob', 'lastname': 'wonderland'}
        self.dird_client.directories.reverse.return_value = {'display': 'Bob',
                                                             'fields': lookup_result}
        mock_dao.find_by_incall_id.return_value.xivo_user_uuid = 'user_uuid'

        self.agi.get_variable.side_effect = [0, sentinel.agi_variable]

        callerid_forphones(self.agi, Mock(), Mock())

        self.dird_client.directories.reverse.assert_called_once_with(
            profile='default',
            user_uuid='user_uuid',
            exten=self.agi.env['agi_callerid'],
            tenant_uuid=sentinel.agi_variable,
        )

        expected_callerid = '"Bob" <5555551234>'
        self.agi.set_callerid.assert_called_once_with(expected_callerid)
        _, set_var_result = self.agi.set_variable.call_args[0]
        for key, value in lookup_result.iteritems():
            s = '%s: %s' % (key, value)
            assert_that(set_var_result, contains_string(s))

    @patch('wazo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_when_dao_return_none(self, mock_dao):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        self.dird_client.directories.reverse.return_value = {'display': None}
        mock_dao.find_by_incall_id.return_value = None

        self.agi.get_variable.side_effect = [0, sentinel.agi_variable]

        callerid_forphones(self.agi, Mock(), Mock())

        self.dird_client.directories.reverse.assert_called_once_with(
            profile='default',
            user_uuid=FAKE_XIVO_USER_UUID,
            exten=self.agi.env['agi_callerid'],
            tenant_uuid=sentinel.agi_variable,
        )

        assert_that(self.agi.set_callerid.call_count, equal_to(0))

    def test_that_callerid_forphones_never_raises(self):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        self.dird_client.directories.reverse.side_effect = AssertionError('Should not raise')

        callerid_forphones(self.agi, Mock(), Mock())
