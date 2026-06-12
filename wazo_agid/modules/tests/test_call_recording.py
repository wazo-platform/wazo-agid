# Copyright 2021-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from unittest import TestCase
from unittest.mock import Mock, call, patch

from wazo_agid import dialplan_variables as dv

from ..call_recording import record_answered, record_caller, start_mix_monitor

RECORD_PENDING = f'__{dv.RECORD_PENDING}'
RECORD_TARGET_CHANNEL = f'__{dv.RECORD_TARGET_CHANNEL}'


class TestRecordCaller(TestCase):
    def setUp(self):
        self.agi = Mock()
        self.agi.get_variable = Mock()
        self.agi.env = {'agi_uniqueid': 'caller-channel-id'}
        self.cursor = Mock()

    def assert_recording_deferred(self):
        self.agi.set_variable.assert_any_call(RECORD_PENDING, '1')
        self.agi.set_variable.assert_any_call(
            RECORD_TARGET_CHANNEL, 'caller-channel-id'
        )

    def assert_recording_not_deferred(self):
        self.agi.set_variable.assert_not_called()

    def test_record_caller_does_not_start_recording_when_already_recording(self):
        self.agi.get_variable.return_value = '1'

        record_caller(self.agi, self.cursor, [])

        self.assert_recording_not_deferred()

    def test_record_caller_does_not_start_recording_when_no_user_id_or_uuid(self):
        agi_variables = {
            'WAZO_CALL_RECORD_ACTIVE': '',
            'WAZO_USERID': '',
            'WAZO_USERUUID': '',
        }
        self.agi.get_variable.side_effect = agi_variables.get

        record_caller(self.agi, self.cursor, [])

        calls = [
            call('WAZO_CALL_RECORD_ACTIVE'),
            call('WAZO_USERUUID'),
            call('WAZO_USERID'),
        ]
        self.agi.get_variable.assert_has_calls(calls)

        self.assert_recording_not_deferred()

    @patch('wazo_agid.objects.User')
    def test_record_caller_defers_recording_fallback_to_user_id_when_no_uuid(
        self, user
    ):
        agi_variables = {
            'WAZO_CALL_RECORD_ACTIVE': '',
            'WAZO_USERID': '1',
            'WAZO_USERUUID': '',
            dv.OUTCALL_ID: '',
        }
        self.agi.get_variable.side_effect = agi_variables.get
        user.return_value = Mock(
            call_record_outgoing_internal_enabled=True,
            call_record_outgoing_external_enabled=False,
        )

        record_caller(self.agi, self.cursor, [])

        calls = [call('WAZO_CALL_RECORD_ACTIVE'), call('WAZO_USERUUID')]
        self.agi.get_variable.assert_has_calls(calls)

        self.assert_recording_deferred()

    @patch('wazo_agid.objects.User')
    def test_record_caller_does_not_record_when_not_an_outcall(self, user):
        agi_variables = {
            'WAZO_CALL_RECORD_ACTIVE': '',
            'WAZO_USERUUID': 'the-users-uuid',
            dv.OUTCALL_ID: '',
        }
        self.agi.get_variable.side_effect = agi_variables.get
        user.return_value = Mock(
            call_record_outgoing_internal_enabled=False,
            call_record_outgoing_external_enabled=False,
        )

        record_caller(self.agi, self.cursor, [])

        calls = [
            call('WAZO_CALL_RECORD_ACTIVE'),
            call('WAZO_USERUUID'),
            call(dv.OUTCALL_ID),
        ]
        self.agi.get_variable.assert_has_calls(calls)

        self.assert_recording_not_deferred()

    @patch('wazo_agid.objects.User')
    def test_record_caller_does_not_record_when_an_outcall_but_disabled(self, user):
        agi_variables = {
            'WAZO_CALL_RECORD_ACTIVE': '',
            'WAZO_USERUUID': 'the-users-uuid',
            dv.OUTCALL_ID: '1',
        }
        self.agi.get_variable.side_effect = agi_variables.get
        user.return_value = Mock(
            call_record_outgoing_internal_enabled=False,
            call_record_outgoing_external_enabled=False,
        )

        record_caller(self.agi, self.cursor, [])

        calls = [
            call('WAZO_CALL_RECORD_ACTIVE'),
            call('WAZO_USERUUID'),
            call(dv.OUTCALL_ID),
        ]
        self.agi.get_variable.assert_has_calls(calls)

        self.assert_recording_not_deferred()

    @patch('wazo_agid.objects.User')
    def test_record_caller_records_when_an_outcall_and_enabled(self, user):
        agi_variables = {
            'WAZO_CALL_RECORD_ACTIVE': '',
            'WAZO_USERUUID': 'the-users-uuid',
            dv.OUTCALL_ID: '1',
        }
        self.agi.get_variable.side_effect = agi_variables.get
        user.return_value = Mock(
            call_record_outgoing_internal_enabled=False,
            call_record_outgoing_external_enabled=True,
        )

        record_caller(self.agi, self.cursor, [])

        calls = [
            call('WAZO_CALL_RECORD_ACTIVE'),
            call('WAZO_USERUUID'),
            call(dv.OUTCALL_ID),
        ]
        self.agi.get_variable.assert_has_calls(calls)

        self.assert_recording_deferred()

    @patch('wazo_agid.objects.User')
    def test_record_caller_does_not_record_when_an_outcall_but_internal_enabled(
        self, user
    ):
        agi_variables = {
            'WAZO_CALL_RECORD_ACTIVE': '',
            'WAZO_USERUUID': 'the-users-uuid',
            dv.OUTCALL_ID: '1',
        }
        self.agi.get_variable.side_effect = agi_variables.get
        user.return_value = Mock(
            call_record_outgoing_internal_enabled=True,
            call_record_outgoing_external_enabled=False,
        )

        record_caller(self.agi, self.cursor, [])

        calls = [
            call('WAZO_CALL_RECORD_ACTIVE'),
            call('WAZO_USERUUID'),
            call(dv.OUTCALL_ID),
        ]
        self.agi.get_variable.assert_has_calls(calls)

        self.assert_recording_not_deferred()

    @patch('wazo_agid.objects.User')
    def test_record_caller_records_when_not_an_outcall_and_internal_enabled(self, user):
        agi_variables = {
            'WAZO_CALL_RECORD_ACTIVE': '',
            'WAZO_USERUUID': 'the-users-uuid',
            dv.OUTCALL_ID: '',
        }
        self.agi.get_variable.side_effect = agi_variables.get
        user.return_value = Mock(
            call_record_outgoing_internal_enabled=True,
            call_record_outgoing_external_enabled=False,
        )

        record_caller(self.agi, self.cursor, [])

        calls = [
            call('WAZO_CALL_RECORD_ACTIVE'),
            call('WAZO_USERUUID'),
            call(dv.OUTCALL_ID),
        ]
        self.agi.get_variable.assert_has_calls(calls)

        self.assert_recording_deferred()

    @patch('wazo_agid.objects.User')
    def test_record_caller_records_when_an_outcall_and_all_enabled(self, user):
        agi_variables = {
            'WAZO_CALL_RECORD_ACTIVE': '',
            'WAZO_USERUUID': 'the-users-uuid',
            dv.OUTCALL_ID: '1',
        }
        self.agi.get_variable.side_effect = agi_variables.get
        user.return_value = Mock(
            call_record_outgoing_internal_enabled=True,
            call_record_outgoing_external_enabled=True,
        )

        record_caller(self.agi, self.cursor, [])

        calls = [
            call('WAZO_CALL_RECORD_ACTIVE'),
            call('WAZO_USERUUID'),
            call(dv.OUTCALL_ID),
        ]
        self.agi.get_variable.assert_has_calls(calls)

        self.assert_recording_deferred()

    @patch('wazo_agid.objects.User')
    def test_record_caller_records_when_not_an_outcall_and_all_enabled(self, user):
        agi_variables = {
            'WAZO_CALL_RECORD_ACTIVE': '',
            'WAZO_USERUUID': 'the-users-uuid',
            dv.OUTCALL_ID: '',
        }
        self.agi.get_variable.side_effect = agi_variables.get
        user.return_value = Mock(
            call_record_outgoing_internal_enabled=True,
            call_record_outgoing_external_enabled=True,
        )

        record_caller(self.agi, self.cursor, [])

        calls = [
            call('WAZO_CALL_RECORD_ACTIVE'),
            call('WAZO_USERUUID'),
            call(dv.OUTCALL_ID),
        ]
        self.agi.get_variable.assert_has_calls(calls)

        self.assert_recording_deferred()


class TestStartMixMonitor(TestCase):
    def setUp(self):
        self.agi = Mock()
        self.cursor = Mock()

    def test_does_not_defer_when_already_recording(self):
        self.agi.get_variable.return_value = '1'

        start_mix_monitor(self.agi, self.cursor, [])

        self.agi.set_variable.assert_not_called()

    def test_defers_recording_when_not_already_recording(self):
        self.agi.get_variable.return_value = ''

        start_mix_monitor(self.agi, self.cursor, [])

        self.agi.set_variable.assert_called_once_with(RECORD_PENDING, '1')


class TestRecordAnswered(TestCase):
    def setUp(self):
        self.calld = Mock()
        self.agi = Mock()
        self.agi.env = {'agi_uniqueid': 'answered-channel-id'}
        self.agi.config = {'calld': {'client': self.calld}}
        self.cursor = Mock()

    def test_does_nothing_when_no_recording_pending(self):
        self.agi.get_variable.side_effect = {dv.RECORD_PENDING: ''}.get

        record_answered(self.agi, self.cursor, [])

        self.calld.calls.start_record.assert_not_called()

    def test_does_nothing_when_already_recording(self):
        self.agi.get_variable.side_effect = {
            dv.RECORD_PENDING: '1',
            'WAZO_CALL_RECORD_ACTIVE': '1',
        }.get

        record_answered(self.agi, self.cursor, [])

        self.calld.calls.start_record.assert_not_called()

    def test_starts_recording_on_target_channel(self):
        self.agi.get_variable.side_effect = {
            dv.RECORD_PENDING: '1',
            'WAZO_CALL_RECORD_ACTIVE': '',
            dv.RECORD_TARGET_CHANNEL: 'caller-channel-id',
            dv.TENANT_UUID: 'the-tenant-uuid',
        }.get

        record_answered(self.agi, self.cursor, [])

        self.calld.calls.start_record.assert_called_once_with(
            'caller-channel-id', tenant_uuid='the-tenant-uuid'
        )

    def test_starts_recording_on_own_channel_when_no_target(self):
        self.agi.get_variable.side_effect = {
            dv.RECORD_PENDING: '1',
            'WAZO_CALL_RECORD_ACTIVE': '',
            dv.RECORD_TARGET_CHANNEL: '',
            dv.TENANT_UUID: 'the-tenant-uuid',
        }.get

        record_answered(self.agi, self.cursor, [])

        self.calld.calls.start_record.assert_called_once_with(
            'answered-channel-id', tenant_uuid='the-tenant-uuid'
        )
