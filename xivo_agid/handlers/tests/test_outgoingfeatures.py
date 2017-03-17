# -*- coding: utf-8 -*-

# Copyright 2013-2017 The Wazo Authors  (see the AUTHORS file)
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
from hamcrest.core import equal_to
from mock import Mock, call, patch
from xivo_agid.handlers.outgoingfeatures import OutgoingFeatures
from xivo_agid import objects


class OutCallBuilder(object):

    def __init__(self):
        self._internal = 0
        self.callerId = ''

    def withCallerId(self, callerId):
        self.callerId = callerId
        return self

    def internal(self):
        self._internal = 1
        return self

    def external(self):
        self._internal = 0
        return self

    def build(self):
        outcall = Mock(objects.Outcall)
        outcall.callerid = self.callerId
        outcall.internal = self._internal
        return outcall


class UserBuilder(object):

    def __init__(self):
        self._caller_id = '"John"'
        self._out_caller_id = 'default'
        self._userfield = None

    def withCallerId(self, caller_id):
        self._caller_id = caller_id
        return self

    def withDefaultOutCallerId(self):
        self._out_caller_id = 'default'
        return self

    def withAnonymousOutCallerId(self):
        self._out_caller_id = 'anonymous'
        return self

    def withCustomOutCallerId(self, caller_id):
        self._out_caller_id = caller_id
        return self

    def withUserField(self, userfield):
        self._userfield = userfield
        return self

    def build(self):
        user = Mock(objects.User)
        user.callerid = self._caller_id
        user.outcallerid = self._out_caller_id
        user.userfield = self._userfield
        return user


def an_outcall():
    return OutCallBuilder()


def a_user():
    return UserBuilder()


class TestOutgoingFeatures(unittest.TestCase):

    def setUp(self):
        config = {'call_recording': {'filename_template': '{{ mock }}',
                                     'filename_extension': 'wav'}}
        self._agi = Mock(config=config)
        self._cursor = Mock()
        self._args = Mock()
        self.outgoing_features = OutgoingFeatures(self._agi, self._cursor, self._args)

    def test_set_userfield(self):
        userfield = 'CP1234'
        user = a_user().withUserField(userfield).build()
        outcall = an_outcall().build()

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_userfield()

        self._agi.set_variable.assert_called_once_with('CHANNEL(userfield)', userfield)

    def test_set_userfield_empty(self):
        user = a_user().build()
        outcall = an_outcall().build()

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_userfield()

        assert_that(self._agi.set_variable.call_count, equal_to(0), 'Set variable call count')

    def test_set_userfield_no_user_no_error(self):
        outcall = an_outcall().build()

        self.outgoing_features.outcall = outcall

        self.outgoing_features._set_userfield()

    @patch('xivo_agid.objects.CallerID.set')
    def test_set_caller_id_outcall_internal(self, mock_set_caller_id):
        user = (a_user()
                .build())
        outcall = (an_outcall()
                   .internal()
                   .build())

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        self.assertFalse(mock_set_caller_id.called)

    @patch('xivo_agid.objects.CallerID.set')
    def test_set_caller_id_no_user_and_outcall_external(self, mock_set_caller_id):
        user = None
        outcall = (an_outcall()
                   .external()
                   .build())

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        self.assertFalse(mock_set_caller_id.called)

    @patch('xivo_agid.objects.CallerID.set')
    def test_set_caller_id_no_user_and_outcall_external_caller_id(self, mock_set_caller_id):
        user = None
        outcall = (an_outcall()
                   .external()
                   .withCallerId('27857218')
                   .build())

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        mock_set_caller_id.assert_called_once_with(self._agi, '27857218')

    @patch('xivo_agid.objects.CallerID.set')
    def test_set_caller_id_user_default_and_outcall_external(self, mock_set_caller_id):
        user = (a_user()
                .withDefaultOutCallerId()
                .build())
        outcall = (an_outcall()
                   .external()
                   .build())

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        self.assertFalse(mock_set_caller_id.called)

    @patch('xivo_agid.objects.CallerID.set')
    def test_set_caller_id_user_default_and_outcall_external_caller_id(self, mock_set_caller_id):
        user = (a_user()
                .withDefaultOutCallerId()
                .build())
        outcall = (an_outcall()
                   .external()
                   .withCallerId('27857218')
                   .build())

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        mock_set_caller_id.assert_called_once_with(self._agi, '27857218')

    @patch('xivo_agid.objects.CallerID.set')
    def test_set_caller_id_user_anonymous_and_outcall_external(self, mock_set_caller_id):
        user = (a_user()
                .withAnonymousOutCallerId()
                .build())
        outcall = (an_outcall()
                   .external()
                   .build())

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        expected_calls = [
            call('CALLERID(name-pres)', 'prohib'),
            call('CALLERID(num-pres)', 'prohib'),
        ]
        self.assertEqual(self._agi.set_variable.call_args_list, expected_calls)
        self.assertFalse(mock_set_caller_id.called)

    @patch('xivo_agid.objects.CallerID.set')
    def test_set_caller_id_user_anonymous_and_outcall_external_caller_id(self, mock_set_caller_id):
        user = (a_user()
                .withAnonymousOutCallerId()
                .build())
        outcall = (an_outcall()
                   .external()
                   .withCallerId('27857218')
                   .build())

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        expected_calls = [
            call('CALLERID(name-pres)', 'prohib'),
            call('CALLERID(num-pres)', 'prohib'),
        ]
        self.assertEqual(self._agi.set_variable.call_args_list, expected_calls)
        self.assertFalse(mock_set_caller_id.called)

    @patch('xivo_agid.objects.CallerID.set')
    def test_set_caller_id_user_custom_and_outcall_external(self, mock_set_caller_id):
        user = (a_user()
                .withCustomOutCallerId('"Custom1"')
                .build())
        outcall = (an_outcall()
                   .external()
                   .build())

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        mock_set_caller_id.assert_called_once_with(self._agi, '"Custom1"')

    @patch('xivo_agid.objects.CallerID.set')
    def test_set_caller_id_user_custom_and_outcall_external_caller_id(self, mock_set_caller_id):
        user = (a_user()
                .withCustomOutCallerId('"Custom1"')
                .build())
        outcall = (an_outcall()
                   .external()
                   .withCallerId('27857218')
                   .build())

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        mock_set_caller_id.assert_called_once_with(self._agi, '"Custom1"')

    def test_retreive_outcall(self):
        outcall = Mock(objects.Outcall)
        self.outgoing_features.outcall = outcall
        self.outgoing_features.dialpattern_id = 23

        self.outgoing_features._retrieve_outcall()

        outcall.retrieve_values.assert_called_once_with(23)
