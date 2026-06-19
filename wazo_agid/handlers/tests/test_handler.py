# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest import TestCase
from unittest.mock import Mock

from wazo_agid import dialplan_variables as dv

from ..handler import Handler

RECORD_PENDING = f'__{dv.RECORD_PENDING}'


class TestRecordPendingCaller(TestCase):
    def setUp(self):
        self.calld = Mock()
        self.agi = Mock()
        self.agi.env = {'agi_uniqueid': 'callee-channel-id'}
        self.agi.config = {'calld': {'client': self.calld}}
        self.handler = Handler(self.agi, Mock(), Mock())

    def test_does_nothing_when_no_recording_pending(self):
        self.agi.get_variable.side_effect = {dv.RECORD_PENDING: ''}.get

        assert self.handler.record_pending_caller() is False
        self.calld.calls.start_record.assert_not_called()

    def test_does_nothing_when_already_recording(self):
        self.agi.get_variable.side_effect = {
            dv.RECORD_PENDING: '1',
            dv.CALL_RECORD_ACTIVE: '1',
        }.get

        assert self.handler.record_pending_caller() is False
        self.calld.calls.start_record.assert_not_called()

    def test_starts_recording_on_target_and_consumes_flag(self):
        self.agi.get_variable.side_effect = {
            dv.RECORD_PENDING: '1',
            dv.CALL_RECORD_ACTIVE: '',
            dv.RECORD_TARGET_CHANNEL: 'caller-channel-id',
            dv.TENANT_UUID: 'the-tenant-uuid',
        }.get

        assert self.handler.record_pending_caller() is True
        self.calld.calls.start_record.assert_called_once_with(
            'caller-channel-id', tenant_uuid='the-tenant-uuid'
        )
        self.agi.set_variable.assert_called_once_with(RECORD_PENDING, '')

    def test_does_not_consume_flag_when_start_fails(self):
        self.agi.get_variable.side_effect = {
            dv.RECORD_PENDING: '1',
            dv.CALL_RECORD_ACTIVE: '',
            dv.RECORD_TARGET_CHANNEL: 'caller-channel-id',
            dv.TENANT_UUID: 'the-tenant-uuid',
        }.get
        self.calld.calls.start_record.side_effect = Exception('boom')

        assert self.handler.record_pending_caller() is False
        self.agi.set_variable.assert_not_called()
