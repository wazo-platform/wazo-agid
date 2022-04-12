# -*- coding: utf-8 -*-
# Copyright 2017-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import (
    assert_that,
    equal_to,
)
from mock import (Mock, patch, sentinel as s)

from ..helpers import (
    build_sip_interface,
    _is_mobile_reachable as is_mobile_and_reachable,
    requests,
    _has_mobile_connection as has_mobile_connection,
)

ABCD_INTERFACE = 'PJSIP/ycetqvtr/sip:n753iqfr@127.0.0.1:44530;transport=ws&PJSIP/ycetqvtr/sip:b6405ov4@127.0.0.1:44396;transport=ws'


class TestBuildSIPInterface(unittest.TestCase):

    def setUp(self):
        self.agi = Mock()
        self.auth_client = Mock()
        self.agi.config = {'auth': {'client': self.auth_client}}
        self.channel_variables = {}
        self.agi.get_variable.side_effect = lambda var: self.channel_variables.get(var, '')

    @patch('wazo_agid.helpers._is_webrtc', Mock(return_value=False))
    @patch('wazo_agid.helpers._has_mobile_connection', Mock(return_value=False))
    def test_not_connected_no_webrtc(self):
        aor_name = 'foobar'

        interface = build_sip_interface(self.agi, s.user_uuid, aor_name)

        self.assertEqual(interface, 'PJSIP/foobar')

    @patch('wazo_agid.helpers._is_webrtc', Mock(return_value=True))
    @patch('wazo_agid.helpers._is_mobile_reachable', Mock(return_value=False))
    @patch('wazo_agid.helpers._has_mobile_connection', Mock(return_value=True))
    def test_mobile_connection_webrtc_not_registered(self):
        aor_name = 'abcd'

        interface = build_sip_interface(self.agi, s.user_uuid, aor_name)

        self.assertEqual(interface, 'Local/abcd@wazo_wait_for_registration')

    @patch('wazo_agid.helpers._is_webrtc', Mock(return_value=True))
    @patch('wazo_agid.helpers._is_mobile_reachable', Mock(return_value=True))
    def test_mobile_connection_webrtc_mobile_registered(self):
        self.channel_variables['PJSIP_DIAL_CONTACTS(abcd)'] = ABCD_INTERFACE
        aor_name = 'abcd'

        interface = build_sip_interface(self.agi, s.user_uuid, aor_name)

        self.assertEqual(interface, ABCD_INTERFACE)

    @patch('wazo_agid.helpers._is_webrtc', Mock(return_value=True))
    @patch('wazo_agid.helpers._is_mobile_reachable', Mock(return_value=True))
    def test_no_mobile_connection_webrtc_mobile_not_registered(self):
        self.channel_variables['PJSIP_DIAL_CONTACTS(abcd)'] = ABCD_INTERFACE
        aor_name = 'abcd'

        interface = build_sip_interface(self.agi, s.user_uuid, aor_name)

        self.assertEqual(interface, ABCD_INTERFACE)

    @patch('wazo_agid.helpers._is_webrtc', Mock(return_value=True))
    @patch('wazo_agid.helpers._is_mobile_reachable', Mock(return_value=True))
    @patch('wazo_agid.helpers._has_mobile_connection', Mock(return_value=False))
    def test_connected(self):
        self.channel_variables['PJSIP_DIAL_CONTACTS(abcd)'] = ABCD_INTERFACE
        aor_name = 'abcd'

        interface = build_sip_interface(self.agi, s.user_uuid, aor_name)

        self.assertEqual(interface, ABCD_INTERFACE)


class TestIsRegisteredAndMobile(unittest.TestCase):

    def test_no_registered_contacts(self):
        agi = Mock()
        agi.get_variable.return_value = ''

        result = is_mobile_and_reachable(agi, 'name')

        assert_that(result, equal_to(False))

    def test_one_contact_not_mobile(self):
        def get_variable(key):
            variables = {
                'PJSIP_AOR(name,contact)': 'the-contact',
            }
            return variables.get(key, '')

        agi = Mock()
        agi.get_variable.side_effect = get_variable

        result = is_mobile_and_reachable(agi, 'name')

        assert_that(result, equal_to(False))

    def test_multiple_contacts_no_mobile(self):
        def get_variable(key):
            variables = {
                'PJSIP_AOR(name,contact)': 'contact;1,contact;2,contact;3',
            }
            return variables.get(key, '')

        agi = Mock()
        agi.get_variable.side_effect = get_variable

        result = is_mobile_and_reachable(agi, 'name')

        assert_that(result, equal_to(False))

    def test_multiple_contacts_one_mobile_and_reachable(self):
        def get_variable(key):
            variables = {
                'PJSIP_AOR(name,contact)': 'contact;1,contact;2,contact;3',
                'PJSIP_CONTACT(contact;1,mobility)': 'mobile',
                'PJSIP_CONTACT(contact;1,status)': 'Unreachable',
                'PJSIP_CONTACT(contact;3,mobility)': 'mobile',
                'PJSIP_CONTACT(contact;3,status)': 'Reachable',
            }
            return variables.get(key, '')

        agi = Mock()
        agi.get_variable.side_effect = get_variable

        result = is_mobile_and_reachable(agi, 'name')

        assert_that(result, equal_to(True))


class TestHasMobileConnection(unittest.TestCase):

    def setUp(self):
        self.agi = Mock()
        self.auth_client = Mock()
        self.agi.config = {'auth': {'client': self.auth_client}}

    def test_auth_error(self):
        self.auth_client.token.list.side_effect = requests.HTTPError
        self.auth_client.users.get_sessions.side_effect = requests.HTTPError

        result = has_mobile_connection(self.agi, s.user_uuid)

        assert_that(result, equal_to(False))
        self.agi.set_variable.assert_not_called()

    def test_no_mobile_connections_no_session(self):
        self.auth_client.token.list.return_value = {'items': [], 'filtered': 0, 'total': 42}
        self.auth_client.users.get_sessions.return_value = {'items': [{'mobile': False}, {'mobile': False}]}

        result = has_mobile_connection(self.agi, s.user_uuid)

        assert_that(result, equal_to(False))
        self.agi.set_variable.assert_not_called()

    def test_with_mobile_connections(self):
        self.auth_client.token.list.return_value = {
            'items': [{'mobile': True}, {'mobile': True}],
            'filtered': 2,
            'total': 42,
        }

        result = has_mobile_connection(self.agi, s.user_uuid)

        assert_that(result, equal_to(True))
        self.agi.set_variable.called_once_with('WAZO_MOBILE_CONNECTION', True)

    def test_mobile_session_only(self):
        self.auth_client.token.list.return_value = {'items': [], 'filtered': 0, 'total': 42}
        self.auth_client.users.get_sessions.return_value = {'items': [{'mobile': False}, {'mobile': True}]}

        result = has_mobile_connection(self.agi, s.user_uuid)

        assert_that(result, equal_to(True))
        self.agi.set_variable.called_once_with('WAZO_MOBILE_CONNECTION', True)
