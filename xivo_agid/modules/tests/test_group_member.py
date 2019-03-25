# -*- coding: utf-8 -*-
# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import (
    assert_that,
    calling,
    contains,
    empty,
)
from mock import Mock
from requests import HTTPError
from xivo_agid.fastagi import FastAGI
from xivo_test_helpers.hamcrest.raises import raises

from ..group_member_add_remove import (
    _get_sibling_interfaces,
    UnknownLine,
    UnknownUser,
)


class TestGetSiblingInterfaces(unittest.TestCase):

    def setUp(self):
        self.agi = Mock(FastAGI)
        self.confd_client = Mock()
        self.agi.config = {'confd': {'client': self.confd_client}}
        self.confd_client.lines.get.return_value = {
            'name': 'test',
            'extensions': [
                {
                    'exten': '1234',
                    'context': 'default',
                }
            ],
            'users': [
                {
                    'uuid': 'abcdef',
                }
            ],
        }
        self.agi.get_variable.return_value = 'PJSIP/test'

    def test_get_sibling_interfaces_unknown_line(self):
        line_id = 12
        self.confd_client.lines.get.side_effect = HTTPError(response=Mock(status_code=404))

        assert_that(calling(_get_sibling_interfaces).with_args(self.agi, line_id),
                    raises(UnknownLine))

    def test_get_sibling_interfaces_line_has_no_extension(self):
        line_id = 12
        self.confd_client.lines.get.return_value = {
            'name': 'test',
            'extensions': [],
            'users': []
        }

        result = _get_sibling_interfaces(self.agi, line_id)

        assert_that(result, empty())

    def test_get_sibling_interfaces_line_has_no_user(self):
        line_id = 12
        self.confd_client.lines.get.return_value = {
            'name': 'test',
            'extensions': [
                {
                    'exten': '1234',
                    'context': 'default',
                }
            ],
            'users': []
        }

        result = _get_sibling_interfaces(self.agi, line_id)

        assert_that(result, empty())

    def test_get_sibling_interfaces_unknown_user(self):
        line_id = 12
        self.confd_client.users.get.side_effect = HTTPError(response=Mock(status_code=404))

        assert_that(calling(_get_sibling_interfaces).with_args(self.agi, line_id),
                    raises(UnknownUser))

    def test_get_sibling_interfaces(self):
        line_id = 12
        self.confd_client.users.get.return_value = {
            'lines': [
                {
                    'name': 'sip-line',
                    'extensions': [
                        {
                            'exten': '1234',
                            'context': 'default',
                        },
                    ],
                    'endpoint_sip': {
                        'username': 'sip-line',
                    },
                    'endpoint_sccp': None,
                },
                {
                    'name': 'sccp-line',
                    'extensions': [
                        {
                            'exten': '1234',
                            'context': 'default',
                        },
                    ],
                    'endpoint_sip': None,
                    'endpoint_sccp': {
                        'id': 543,
                    },
                },
                {
                    'name': 'different-exten',
                    'extensions': [
                        {
                            'exten': '9999',
                            'context': 'default',
                        },
                    ],
                    'endpoint_sip': None,
                    'endpoint_sccp': {
                        'id': 543,
                    },
                },
                {
                    'name': 'no-endpoint',
                    'extensions': [
                        {
                            'exten': '1234',
                            'context': 'default',
                        },
                    ],
                    'endpoint_sip': None,
                    'endpoint_sccp': None,
                },
            ]
        }
        self.agi.get_variable.return_value = 'PJSIP/sip-line'

        result = _get_sibling_interfaces(self.agi, line_id)

        assert_that(result, contains('PJSIP/sip-line', 'SCCP/sccp-line'))

    def test_get_sibling_interfaces_pjsip_multicontact(self):
        line_id = 12
        self.confd_client.users.get.return_value = {
            'lines': [
                {
                    'name': 'sip-line',
                    'extensions': [
                        {
                            'exten': '1234',
                            'context': 'default',
                        },
                    ],
                    'endpoint_sip': {
                        'username': 'sip-line',
                    },
                    'endpoint_sccp': None,
                },
            ]
        }
        self.agi.get_variable.return_value = 'PJSIP/sip-line1&PJSIP/sip-line2'

        result = _get_sibling_interfaces(self.agi, line_id)

        assert_that(result, contains('PJSIP/sip-line1', 'PJSIP/sip-line2'))
