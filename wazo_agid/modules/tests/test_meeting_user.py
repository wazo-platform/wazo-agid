# Copyright 2021-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import unittest
from unittest.mock import Mock

from wazo_agid.fastagi import FastAGI

from ..meeting_user import meeting_user


class TestMeetingUser(unittest.TestCase):
    def setUp(self):
        self.agi = Mock(FastAGI)
        self.cursor = Mock()

    def test_invalid_args(self):
        invalid_args = [
            [],
            [42],
            ['wazo-meeting-42'],
            None,
        ]
        self.cursor.fetchone.side_effect = LookupError

        for args in invalid_args:
            meeting_user(self.agi, self.cursor, args)  # type: ignore
            self.agi.stream_file.assert_called_once_with('invalid')
            self.agi.stream_file.reset_mock()

    def test_unknown_meeting(self):
        self.cursor.fetchone.side_effect = LookupError

        meeting_user(
            self.agi, self.cursor, ['wazo-meeting-99999999-9999-4999-9999-999999999999']
        )
        self.agi.stream_file.assert_called_once_with('invalid')
