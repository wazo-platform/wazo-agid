# Copyright 2023-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from unittest import TestCase

from hamcrest import assert_that, is_

from ..objects import CallerID, VMBox


class TestCallerID(TestCase):
    def test_parse(self) -> None:
        scenarios: list[tuple[str, tuple[str, str]]] = [
            ('"Foo Bar" <123>', ('Foo Bar', '123')),
            ('"Foo Bar" <#42>', ('Foo Bar', '#42')),
            ('234', ('234', '234')),
            ('+456', ('+456', '+456')),
            ('*10', ('*10', '*10')),
            ('SingleWord <789>', ('SingleWord', '789')),
            ('SingleWord <*10>', ('SingleWord', '*10')),
            ('"Foo Bar"', ('Foo Bar', '')),
        ]

        for caller_id, expected in scenarios:
            result = CallerID.parse(caller_id)
            assert result == expected

        error_scenarios = [
            '#42',
            '"" <345>',
            '"Foo Bar" <>',
            'Foo Bar',
            '',
            '""',
            '"" 42',
        ]

        for caller_id in error_scenarios:
            with self.assertRaises(ValueError):
                CallerID.parse(caller_id)


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
