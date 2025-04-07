# Copyright 2013-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import unittest
from textwrap import dedent
from unittest.mock import Mock, patch, sentinel

from hamcrest import assert_that, equal_to, is_

from wazo_agid.fastagi import FastAGI
from wazo_agid.modules.callerid_forphones import (
    FAKE_WAZO_USER_UUID,
    callerid_forphones,
    is_phone_number,
)


class TestIsPhoneNumber(unittest.TestCase):
    def test_with_valid_numbers(self):
        # international E134
        assert_that(is_phone_number("+11234567890"), is_(True))
        # example national format
        assert_that(is_phone_number("1234567890"), is_(True))
        # international prefix instead of +
        assert_that(is_phone_number("0011234567890"), is_(True))
        # short alphanumeric extension
        assert_that(is_phone_number("1234"), is_(True))

    def test_not_a_number(self):
        assert_that(is_phone_number('My Name'), is_(False))
        assert_that(is_phone_number('1 is not a number'), is_(False))


class TestCallerIdForPhone(unittest.TestCase):
    def setUp(self):
        self.agi = Mock(FastAGI)
        self.dird_client = Mock()
        self.agi.config = {'dird': {'client': self.dird_client}}
        self.agi.get_variable.return_value = '42'

    def test_callerid_forphones_no_lookup(self):
        self.agi.env = {
            'agi_calleridname': 'Alice',
            'agi_callerid': '5555551234',
        }
        self.dird_client.graphql.query.return_value = {
            'data': {
                'user': {
                    'contacts': {
                        'edges': [
                            {'node': None},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                        ]
                    }
                }
            }
        }

        callerid_forphones(self.agi, Mock(), Mock())

        assert_that(self.dird_client.graphql.query.call_count, equal_to(0))

    @patch('wazo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_on_unknown_cid_name(self, _):
        # Some operators send "unknown" in the caller id name
        self.agi.env = {
            'agi_calleridname': 'unknown',
            'agi_callerid': '5555551234',
        }
        self.dird_client.graphql.query.return_value = {
            'data': {
                'user': {
                    'contacts': {
                        'edges': [
                            {'node': None},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                        ]
                    }
                }
            }
        }

        callerid_forphones(self.agi, Mock(), Mock())

        assert_that(self.dird_client.graphql.query.call_count, equal_to(1))

    @patch('wazo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_on_same_cid_name_and_cid_num(self, _):
        # if cid name is cid number, ignore cid name and lookup
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        self.dird_client.graphql.query.return_value = {
            'data': {
                'user': {
                    'contacts': {
                        'edges': [
                            {'node': None},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                        ]
                    }
                }
            }
        }

        callerid_forphones(self.agi, Mock(), Mock())

        assert_that(self.dird_client.graphql.query.call_count, equal_to(1))

    @patch('wazo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_on_almost_same_cid_name_and_cid_num(self, _):
        # Some operators put a variation of the cid number in the cid name, still lookup
        self.agi.env = {
            'agi_calleridname': '+335555551234',
            'agi_callerid': '00335555551234',
        }
        self.dird_client.graphql.query.return_value = {
            'data': {
                'user': {
                    'contacts': {
                        'edges': [
                            {'node': None},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                        ]
                    }
                }
            }
        }

        callerid_forphones(self.agi, Mock(), Mock())

        assert_that(self.dird_client.graphql.query.call_count, equal_to(1))

    @patch('wazo_agid.modules.callerid_forphones.objects.Tenant')
    @patch('wazo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_no_result(self, mock_dao, mock_tenant):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        self.dird_client.graphql.query.return_value = {
            'data': {
                'user': {
                    'contacts': {
                        'edges': [
                            {'node': None},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                        ]
                    }
                }
            }
        }
        mock_dao.find_by_incall_id.return_value.user_uuid = 'user_uuid'
        mock_tenant.return_value.country = 'CA'

        self.agi.get_variable.side_effect = [0, sentinel.agi_variable]

        callerid_forphones(self.agi, Mock(), Mock())

        query = {
            'query': dedent(
                '''
            query GetExtensFromUser($uuid: String!, $extens: [String!]!) {
                user(uuid: $uuid) {
                    contacts(profile: "default", extens: $extens) {
                        edges {
                            node {
                                wazoReverse
                            }
                        }
                    }
                }
            }'''
            ),
            'variables': {
                'uuid': 'user_uuid',
                'extens': [
                    self.agi.env['agi_callerid'],
                    '+1 555-555-1234',
                    '+15555551234',
                    '(555) 555-1234',
                    '1 (555) 555-1234',
                ],
            },
        }
        self.dird_client.graphql.query.assert_called_once_with(
            query,
            tenant_uuid=sentinel.agi_variable,
        )

        assert_that(self.agi.set_callerid.call_count, equal_to(0))

    @patch('wazo_agid.modules.callerid_forphones.objects.Tenant')
    @patch('wazo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_with_result(self, mock_dao, mock_tenant):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }

        self.dird_client.graphql.query.return_value = {
            'data': {
                'user': {
                    'contacts': {
                        'edges': [
                            {'node': {'wazoReverse': 'Bob'}},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                        ]
                    }
                }
            }
        }

        mock_dao.find_by_incall_id.return_value.user_uuid = 'user_uuid'
        mock_tenant.return_value.country = 'CA'

        self.agi.get_variable.side_effect = [0, sentinel.agi_variable]

        callerid_forphones(self.agi, Mock(), Mock())

        query = {
            'query': dedent(
                '''
            query GetExtensFromUser($uuid: String!, $extens: [String!]!) {
                user(uuid: $uuid) {
                    contacts(profile: "default", extens: $extens) {
                        edges {
                            node {
                                wazoReverse
                            }
                        }
                    }
                }
            }'''
            ),
            'variables': {
                'uuid': 'user_uuid',
                'extens': [
                    self.agi.env['agi_callerid'],
                    '+1 555-555-1234',
                    '+15555551234',
                    '(555) 555-1234',
                    '1 (555) 555-1234',
                ],
            },
        }
        self.dird_client.graphql.query.assert_called_once_with(
            query,
            tenant_uuid=sentinel.agi_variable,
        )

        expected_callerid = '"Bob" <5555551234>'
        self.agi.set_callerid.assert_called_once_with(expected_callerid)

    @patch('wazo_agid.modules.callerid_forphones.objects.Tenant')
    @patch('wazo_agid.modules.callerid_forphones.directory_profile_dao')
    def test_callerid_forphones_when_dao_return_none(self, mock_dao, mock_tenant):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        self.dird_client.graphql.query.return_value = {
            'data': {
                'user': {
                    'contacts': {
                        'edges': [
                            {'node': None},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                            {'node': None},
                        ]
                    }
                }
            }
        }
        mock_dao.find_by_incall_id.return_value = None
        mock_tenant.return_value = None

        self.agi.get_variable.side_effect = [0, sentinel.agi_variable]

        callerid_forphones(self.agi, Mock(), Mock())

        query = {
            'query': dedent(
                '''
            query GetExtensFromUser($uuid: String!, $extens: [String!]!) {
                user(uuid: $uuid) {
                    contacts(profile: "default", extens: $extens) {
                        edges {
                            node {
                                wazoReverse
                            }
                        }
                    }
                }
            }'''
            ),
            'variables': {
                'uuid': FAKE_WAZO_USER_UUID,
                'extens': [self.agi.env['agi_callerid']],
            },
        }
        self.dird_client.graphql.query.assert_called_once_with(
            query,
            tenant_uuid=sentinel.agi_variable,
        )

        assert_that(self.agi.set_callerid.call_count, equal_to(0))

    def test_that_callerid_forphones_never_raises(self):
        self.agi.env = {
            'agi_calleridname': '5555551234',
            'agi_callerid': '5555551234',
        }
        self.dird_client.directories.reverse.side_effect = AssertionError(
            'Should not raise'
        )

        callerid_forphones(self.agi, Mock(), Mock())
