# Copyright 2023-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from unittest import TestCase

from hamcrest import assert_that, is_

from ..objects import CallerID, VMBox


class VMBoxFastInit(VMBox):
    def __init__(self):
        pass


class TestVMBox(TestCase):
    def test_voicemail_has_password_with_no_password(self):
        vmbox = VMBoxFastInit()
        vmbox.password = ''
        vmbox.skipcheckpass = 0

        assert_that(vmbox.has_password(), is_(False))

    def test_voicemail_has_password_with_password(self):
        vmbox = VMBoxFastInit()
        vmbox.password = '1234'
        vmbox.skipcheckpass = 0

        assert_that(vmbox.has_password(), is_(True))

    def test_voicemail_has_password_no_skip_pass(self):
        vmbox = VMBoxFastInit()
        vmbox.password = '1234'
        vmbox.skipcheckpass = 0

        assert_that(vmbox.has_password(), is_(True))

    def test_voicemail_has_password_skip_pass(self):
        vmbox = VMBoxFastInit()
        vmbox.password = '1234'
        vmbox.skipcheckpass = 1

        assert_that(vmbox.has_password(), is_(False))


class TestCallerID(TestCase):
    def test_parse(self):
        test_cases = (
            ('Test <123>', ('Test', '123')),
            ('"Test" <+123>', ('Test', '+123')),
            ('"Test <+123>', None),
            ('Test" <+123>', None),
            ('"Test word   " <+123>', ('Test word   ', '+123')),
            ('Test2 word    <+123>', ('Test2 word', '+123')),
            ('Test3 word    <123>', ('Test3 word', '123')),
            ('  Test4 word    <123>', ('Test4 word', '123')),
            ('a', ('a', None)),
            ('1', ('1', '1')),
            ('+123', ('+123', '+123')),
            ('anonymous', ('anonymous', None)),
            ('', None),
            (None, None),
        )
        for test_case, expected_result in test_cases:
            assert CallerID.parse(test_case) == expected_result
