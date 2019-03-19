# -*- coding: utf-8 -*-
# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import (
    assert_that,
    calling,
    contains,
)
from mock import Mock
from requests import HTTPError
from xivo_agid.fastagi import FastAGI
from xivo_test_helpers.hamcrest.raises import raises

from ..get_user_interfaces import (
    get_user_interfaces,
    UnknownUser,
)


class TestGetUserInterfaces(unittest.TestCase):

    def setUp(self):
        self.agi = Mock(FastAGI)
        self.cursor = Mock()
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

    def test_get_user_interfaces_unknown_user(self):
        user_uuid = 'abcdef'
        self.confd_client.users.get.side_effect = HTTPError(response=Mock(status_code=404))

        assert_that(calling(get_user_interfaces).with_args(self.agi, self.cursor, [user_uuid]),
                    raises(UnknownUser))

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
                    'endpoint_custom': None,
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
                    'endpoint_custom': None,
                },
                {
                    'name': 'custom-line',
                    'extensions': [
                        {
                            'exten': '1234',
                            'context': 'default',
                        },
                    ],
                    'endpoint_sip': None,
                    'endpoint_sccp': None,
                    'endpoint_custom': {
                        'interface': 'DAHDI/custom',
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
                    'endpoint_custom': None,
                },
            ]
        }
        self.agi.get_variable.return_value = 'PJSIP/sip-line'

        result = get_user_interfaces(self.agi, self.cursor, [user_uuid])

        self.agi.set_variable.assert_called_once_with('WAZO_USER_INTERFACES', 'PJSIP/sip-line&SCCP/sccp-line&DAHDI/custom')

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
                    'endpoint_custom': None,
                },
            ]
        }
        self.agi.get_variable.return_value = 'PJSIP/sip-line1&PJSIP/sip-line2'

        get_user_interfaces(self.agi, self.cursor, [user_uuid])

        self.agi.set_variable.assert_called_once_with('WAZO_USER_INTERFACES', 'PJSIP/sip-line1&PJSIP/sip-line2')
