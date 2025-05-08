# Copyright 2024-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest import TestCase
from unittest.mock import Mock, call

from psycopg2.extras import DictCursor

from wazo_agid import dialplan_variables as dv
from wazo_agid.agid import FastAGI

from ..outgoing_callerid_formatter import CallerIDFormatter


class TestOutgoingCallerIdFormatter(TestCase):
    def setUp(self) -> None:
        self.agi = Mock(FastAGI)
        self.cursor = Mock(DictCursor)
        self.args: list[str] = []

        self.handler = CallerIDFormatter(self.agi, self.cursor, self.args)

    def test_no_selected_caller_id(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: '',
            dv.TRUNK_CID_FORMAT: '+E164',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.set_caller_id()

        self.agi.set_variable.assert_not_called()

    def test_selected_going_national(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: '+15551234567',
            dv.TRUNK_CID_FORMAT: 'national',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.set_caller_id()

        self.agi.set_variable.assert_called_once_with(
            'CALLERID(all)',
            '"5551234567" <5551234567>',
        )

    def test_selected_going_E164(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: '+15551234567',
            dv.TRUNK_CID_FORMAT: 'E164',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.set_caller_id()

        self.agi.set_variable.assert_called_once_with(
            'CALLERID(all)',
            '"15551234567" <15551234567>',
        )

    def test_selected_going_plusE164(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: '+15551234567',
            dv.TRUNK_CID_FORMAT: '+E164',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.set_caller_id()

        self.agi.set_variable.assert_called_once_with(
            'CALLERID(all)',
            '"+15551234567" <+15551234567>',
        )

    def test_selected_going_plusE164_cid_name_preserved(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: '"Foobar" <+15551234567>',
            dv.TRUNK_CID_FORMAT: '+E164',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.set_caller_id()

        self.agi.set_variable.assert_called_once_with(
            'CALLERID(all)',
            '"Foobar" <+15551234567>',
        )

    def test_selected_E164_going_plusE164(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: '15551234567',
            dv.TRUNK_CID_FORMAT: '+E164',
            'WAZO_TENANT_COUNTRY': 'CA',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.set_caller_id()

        self.agi.set_variable.assert_called_once_with(
            'CALLERID(all)',
            '"+15551234567" <+15551234567>',
        )

    def test_selected_national_going_plusE164(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: '5551234567',
            dv.TRUNK_CID_FORMAT: '+E164',
            'WAZO_TENANT_COUNTRY': 'CA',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.set_caller_id()

        self.agi.set_variable.assert_called_once_with(
            'CALLERID(all)',
            '"+15551234567" <+15551234567>',
        )

    def test_selected_invalid(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: 'invalid',
            dv.TRUNK_CID_FORMAT: '+E164',
            'WAZO_TENANT_COUNTRY': '',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.set_caller_id()

        self.agi.set_variable.assert_not_called()

    def test_selected_valid_raw(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: '123',
            dv.TRUNK_CID_FORMAT: '+E164',
            'WAZO_TENANT_COUNTRY': '',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.set_caller_id()

        self.agi.set_variable.assert_called_once_with(
            'CALLERID(all)',
            '"123" <123>',
        )

    def test_selected_valid_raw_name_preserved(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: '"Foobar" <123>',
            dv.TRUNK_CID_FORMAT: '+E164',
            'WAZO_TENANT_COUNTRY': '',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.set_caller_id()

        self.agi.set_variable.assert_called_once_with(
            'CALLERID(all)',
            '"Foobar" <123>',
        )

    def test_diversion_going_national(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: '+14189990000',
            dv.TRUNK_CID_FORMAT: 'national',
            dv.DST_REDIRECTING_EXTERN_NUM: '+14189990000',
            'WAZO_TENANT_COUNTRY': 'CA',
            'WAZO_DST_REDIRECTING_EXTERN_NAME': 'Test',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.execute()

        self.agi.set_variable.assert_has_calls(
            [
                call('REDIRECTING(from-num,i)', '4189990000'),
                call('REDIRECTING(from-name,i)', 'Test'),
            ]
        )

    def test_diversion_going_e164(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: '+14189990000',
            dv.TRUNK_CID_FORMAT: 'E164',
            dv.DST_REDIRECTING_EXTERN_NUM: '+14189990000',
            'WAZO_TENANT_COUNTRY': 'CA',
            'WAZO_DST_REDIRECTING_EXTERN_NAME': 'Test',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.execute()

        self.agi.set_variable.assert_has_calls(
            [
                call('REDIRECTING(from-num,i)', '14189990000'),
                call('REDIRECTING(from-name,i)', 'Test'),
            ]
        )

    def test_diversion_going_plus_E164(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: '+14189990000',
            dv.TRUNK_CID_FORMAT: '+E164',
            dv.DST_REDIRECTING_EXTERN_NUM: '+14189990000',
            'WAZO_TENANT_COUNTRY': 'CA',
            'WAZO_DST_REDIRECTING_EXTERN_NAME': 'Test',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.execute()

        self.agi.set_variable.assert_has_calls(
            [
                call('REDIRECTING(from-num,i)', '+14189990000'),
                call('REDIRECTING(from-name,i)', 'Test'),
            ]
        )

    def test_diversion_going_extension(self) -> None:
        channel_vars = {
            dv.SELECTED_CALLER_ID: '+14189990000',
            dv.TRUNK_CID_FORMAT: '+E164',
            dv.DST_REDIRECTING_EXTERN_NUM: '1000',
            'WAZO_TENANT_COUNTRY': 'CA',
            'WAZO_DST_REDIRECTING_EXTERN_NAME': 'Test',
        }
        self.agi.get_variable.side_effect = channel_vars.get

        self.handler.execute()

        self.agi.set_variable.assert_has_calls(
            [
                call('REDIRECTING(from-num,i)', '1000'),
                call('REDIRECTING(from-name,i)', 'Test'),
            ]
        )
