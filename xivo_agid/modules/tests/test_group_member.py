# -*- coding: utf-8 -*-
# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import (
    assert_that,
    contains,
)
from mock import Mock
from xivo_agid.fastagi import FastAGI

from ..group_member import (
    _get_user_interfaces,
)


class TestGetUserInterfaces(unittest.TestCase):

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

    def test_get_user_interfaces(self):
        user_uuid = 'abcdef'
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

        result = _get_user_interfaces(self.agi, user_uuid)

        assert_that(result, contains('PJSIP/sip-line', 'SCCP/sccp-line', 'SCCP/different-exten'))

    def test_get_user_interfaces_pjsip_multicontact(self):
        user_uuid = 'abcdef'
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

        result = _get_user_interfaces(self.agi, user_uuid)

        assert_that(result, contains('PJSIP/sip-line1', 'PJSIP/sip-line2'))
