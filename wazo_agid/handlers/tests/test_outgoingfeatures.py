# Copyright 2013-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import Mock, call, patch

from hamcrest import assert_that
from hamcrest.core import equal_to

from wazo_agid import objects
from wazo_agid.handlers.outgoingfeatures import OutgoingFeatures


class OutCallBuilder:
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


class UserBuilder:
    def __init__(self):
        self._caller_id = '"John"'
        self._out_caller_id = 'default'
        self._userfield = None
        self._musiconhold = None

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

    def withMoh(self, moh):
        self._musiconhold = moh
        return self

    def build(self):
        user = Mock(objects.User)
        user.callerid = self._caller_id
        user.outcallerid = self._out_caller_id
        user.userfield = self._userfield
        user.musiconhold = self._musiconhold
        return user


def an_outcall():
    return OutCallBuilder()


def a_user():
    return UserBuilder()


class TestOutgoingFeatures(unittest.TestCase):
    def setUp(self):
        config = {
            'call_recording': {
                'filename_template': '{{ mock }}',
                'filename_extension': 'wav',
            }
        }
        agi_environment = {'agi_channel': 'PJSIP/my-channel-0001'}
        self._agi = Mock(config=config, env=agi_environment)
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

        assert_that(
            self._agi.set_variable.call_count, equal_to(0), 'Set variable call count'
        )

    def test_set_userfield_no_user_no_error(self):
        outcall = an_outcall().build()

        self.outgoing_features.outcall = outcall

        self.outgoing_features._set_userfield()

    def test_set_user_music_on_hold(self):
        moh = 'a-moh'
        user = a_user().withMoh(moh).build()
        outcall = an_outcall().build()

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_user_music_on_hold()

        self._agi.set_variable.assert_called_once_with('CHANNEL(musicclass)', moh)

    def test_set_user_music_on_hold_empty(self):
        user = a_user().build()
        outcall = an_outcall().build()

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_user_music_on_hold()

        assert_that(
            self._agi.set_variable.call_count, equal_to(0), 'Set variable call count'
        )

    def test_set_user_music_on_hold_no_user_no_error(self):
        outcall = an_outcall().build()

        self.outgoing_features.outcall = outcall

        self.outgoing_features._set_user_music_on_hold()

    @patch('wazo_agid.objects.CallerID.set')
    def test_set_caller_id_outcall_internal(self, mock_set_caller_id):
        user = a_user().build()
        outcall = an_outcall().internal().build()

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        self.assertFalse(mock_set_caller_id.called)

    @patch('wazo_agid.objects.CallerID.set')
    def test_set_caller_id_no_user_and_outcall_external(self, mock_set_caller_id):
        user = None
        outcall = an_outcall().external().build()

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        self.assertFalse(mock_set_caller_id.called)

    @patch('wazo_agid.objects.CallerID.set')
    def test_set_caller_id_no_user_and_outcall_external_caller_id(
        self, mock_set_caller_id
    ):
        user = None
        outcall = an_outcall().external().withCallerId('27857218').build()

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        mock_set_caller_id.assert_called_once_with(self._agi, '27857218')

    @patch('wazo_agid.objects.CallerID.set')
    def test_set_caller_id_user_default_and_outcall_external(self, mock_set_caller_id):
        user = a_user().withDefaultOutCallerId().build()
        outcall = an_outcall().external().build()

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        self.assertFalse(mock_set_caller_id.called)

    @patch('wazo_agid.objects.CallerID.set')
    def test_set_caller_id_user_default_and_outcall_external_caller_id(
        self, mock_set_caller_id
    ):
        user = a_user().withDefaultOutCallerId().build()
        outcall = an_outcall().external().withCallerId('27857218').build()

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        mock_set_caller_id.assert_called_once_with(self._agi, '27857218')

    @patch('wazo_agid.objects.CallerID.set')
    def test_set_caller_id_user_anonymous_and_outcall_external(
        self, mock_set_caller_id
    ):
        user = a_user().withAnonymousOutCallerId().build()
        outcall = an_outcall().external().build()

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        expected_calls = [
            call('CALLERID(pres)', 'prohib'),
            call('WAZO_OUTGOING_ANONYMOUS_CALL', '1'),
        ]
        self.assertEqual(self._agi.set_variable.call_args_list, expected_calls)
        self.assertFalse(mock_set_caller_id.called)

    @patch('wazo_agid.objects.CallerID.set')
    def test_set_caller_id_user_anonymous_and_outcall_external_caller_id(
        self, mock_set_caller_id
    ):
        user = a_user().withAnonymousOutCallerId().build()
        outcall = an_outcall().external().withCallerId('27857218').build()

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        expected_calls = [
            call('CALLERID(pres)', 'prohib'),
            call('WAZO_OUTGOING_ANONYMOUS_CALL', '1'),
            call('_WAZO_OUTCALL_PAI_NUMBER', '27857218'),
        ]
        self.assertEqual(self._agi.set_variable.call_args_list, expected_calls)
        self.assertFalse(mock_set_caller_id.called)

    @patch('wazo_agid.objects.CallerID.set')
    def test_set_caller_id_user_custom_and_outcall_external(self, mock_set_caller_id):
        user = a_user().withCustomOutCallerId('"Custom1"').build()
        outcall = an_outcall().external().build()

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        mock_set_caller_id.assert_called_once_with(self._agi, '"Custom1"')

    @patch('wazo_agid.objects.CallerID.set')
    def test_set_caller_id_user_custom_and_outcall_external_caller_id(
        self, mock_set_caller_id
    ):
        user = a_user().withCustomOutCallerId('"Custom1"').build()
        outcall = an_outcall().external().withCallerId('27857218').build()

        self.outgoing_features.outcall = outcall
        self.outgoing_features.user = user

        self.outgoing_features._set_caller_id()

        mock_set_caller_id.assert_called_once_with(self._agi, '"Custom1"')

    def test_retreive_outcall(self):
        outcall = Mock(objects.Outcall)
        self.outgoing_features.outcall = outcall
        self.outgoing_features.dialpattern_id = '23'

        self.outgoing_features._retrieve_outcall()

        outcall.retrieve_values.assert_called_once_with('23')
