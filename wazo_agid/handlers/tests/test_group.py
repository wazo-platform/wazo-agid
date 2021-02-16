# -*- coding: utf-8 -*-
# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest import TestCase
from mock import Mock, patch
from hamcrest import assert_that, calling, equal_to, raises

from ..group import AnswerHandler


class TestAnswerHandler(TestCase):

    def setUp(self):
        self.agi = Mock()
        self.cursor = Mock()
        self.args = Mock()

        self.handler = AnswerHandler(self.agi, self.cursor, self.args)

    @patch('wazo_agid.handlers.group.objects.User')
    def test_get_user_extension_member(self, User):
        extension = '1001'
        context = 'here'

        chan_name = 'Local/{extension}@{context}-000000001;1'.format(
            extension=extension,
            context=context,
        )
        self.agi.env = {
            'agi_channel': chan_name,
        }

        result = self.handler.get_user()

        assert_that(result, equal_to(User.return_value))
        User.assert_called_once_with(
            self.agi,
            self.cursor,
            exten=extension,
            context=context,
        )

    @patch('wazo_agid.handlers.group.objects.User')
    def test_get_user_user_member(self, User):
        user_uuid = 'e15b4765-719d-40d4-8bdd-ff578e2bef47'
        chan_name = 'Local/{user_uuid}@usersharedlines-00000001;1'.format(
            user_uuid=user_uuid,
        )

        self.agi.env = {
            'agi_channel': chan_name,
        }

        result = self.handler.get_user()

        assert_that(result, equal_to(User.return_value))
        User.assert_called_once_with(self.agi, self.cursor, xid=user_uuid)

    @patch('wazo_agid.handlers.group.objects.User')
    def test_get_user_unknown_user(self, User):
        User.side_effect = LookupError
        chan_name = 'Local/unknown@usersharedlines-00000001;1'
        self.agi.env = {
            'agi_channel': chan_name,
        }

        assert_that(calling(self.handler.get_user), raises(LookupError))

    def test_get_user_how_did_that_happen(self):
        chan_name = 'PJSIP/abc-00000001;1'
        self.agi.env = {
            'agi_channel': chan_name,
        }

        assert_that(calling(self.handler.get_user), raises(LookupError))

    def test_record_call_already_recorded(self):
        chan_vars = {'WAZO_CALL_RECORD_ACTIVE': '1'}
        self.agi.get_variable.side_effect = lambda name: chan_vars.get(name, '')
        user = Mock()

        self.handler.record_call(user)

        self.agi.set_variable.assert_not_called()
        self.agi.appexec.assert_not_called()

    def test_record_call_incoming_internal_enabled(self):
        filename = '/foo/bar.wav'
        chan_vars = {'XIVO_CALLRECORDFILE': filename}
        self.agi.get_variable.side_effect = lambda name: chan_vars.get(name, '')
        user = Mock(
            call_record_incoming_internal_enabled=True,
            call_record_incoming_external_enabled=False,
        )

        self.handler.record_call(user)

        self.agi.set_variable.assert_any_call('__WAZO_CALL_RECORD_ACTIVE', '1')
        self.agi.appexec.assert_called_once_with('MixMonitor', filename)

    def test_record_call_incoming_external_enabled(self):
        filename = '/foo/bar.wav'
        chan_vars = {'XIVO_CALLRECORDFILE': filename}
        self.agi.get_variable.side_effect = lambda name: chan_vars.get(name, '')
        user = Mock(
            call_record_incoming_internal_enabled=False,
            call_record_incoming_external_enabled=True,
        )

        self.handler.record_call(user)

        self.agi.set_variable.assert_any_call('__WAZO_CALL_RECORD_ACTIVE', '1')
        self.agi.appexec.assert_called_once_with('MixMonitor', filename)

    def test_record_call_incoming_disabled(self):
        filename = '/foo/bar.wav'
        chan_vars = {'XIVO_CALLRECORDFILE': filename}
        self.agi.get_variable.side_effect = lambda name: chan_vars.get(name, '')
        user = Mock(
            call_record_incoming_internal_enabled=False,
            call_record_incoming_external_enabled=False,
        )

        self.handler.record_call(user)

        self.agi.set_variable.assert_not_called()
        self.agi.appexec.assert_not_called()
