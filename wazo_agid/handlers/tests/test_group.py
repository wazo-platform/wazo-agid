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

        chan_name = 'Local/{extension}@{context}-0000000a1;1'.format(
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
