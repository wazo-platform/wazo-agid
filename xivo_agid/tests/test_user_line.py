# -*- coding: utf-8 -*-
# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest import TestCase

from mock import Mock
from hamcrest import (
    assert_that,
    calling,
    contains_inanyorder,
    raises,
)

from xivo_agid.objects import (
    UnknownUser,
    UserLine,
)


class TestUserLine(TestCase):

    hints = {
        'abc@usersharedlines': 'pjsip/one&sccp/two&dahdi/i1/55555555&pjsip/two&pjsip/three',
    }

    contacts = {
        'one': 'one-1&one-2',
        'two': 'two-1',
    }

    def setUp(self):
        self.agi = Mock()

        def get_variable(var):
            dialplan_fn, end = var.split('(', 1)
            arg = end.split(')', 1)[0]

            if dialplan_fn == 'HINT':
                return self.hints.get(arg, '')
            elif dialplan_fn == 'PJSIP_DIAL_CONTACTS':
                return self.contacts.get(arg, '')

        self.agi.get_variable = get_variable

    def test_unknown_user(self):
        assert_that(
            calling(UserLine).with_args(self.agi, 'unknown'),
            raises(UnknownUser),
        )

    def test_many_interfaces(self):
        user_line = UserLine(self.agi, 'abc')

        assert_that(user_line.interfaces, contains_inanyorder(
            'sccp/two',
            'dahdi/i1/55555555',
            'one-1',
            'one-2',
            'two-1',
        ))
