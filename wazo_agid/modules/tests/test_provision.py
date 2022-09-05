# -*- coding: UTF-8 -*-
# Copyright 2016-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from mock import Mock

from wazo_agid.modules import provision


class TestDoProvision(unittest.TestCase):

    EMPTY_LIST = {'total': 0, 'items': []}

    def setUp(self):
        self.client = Mock()

    def provision(self, code, ip):
        provision._do_provision(self.client, code, ip)

    def test_given_device_does_not_exist_when_provisioning_then_raises_error(self):
        self.client.devices.list.return_value = self.EMPTY_LIST

        self.assertRaises(Exception, self.provision, "123456", "127.0.0.1")

    def test_given_line_does_not_exist_when_provisioning_then_raises_error(self):
        device = {'id': '1234abcd', 'ip': '127.0.0.1'}
        self.client.devices.list.return_value = {'total': 1, 'items': [device]}
        self.client.lines.list.return_value = self.EMPTY_LIST

        self.assertRaises(Exception, self.provision, "123456", "127.0.0.1")

    def test_given_line_and_device_exist_when_provisioning_then_line_and_device_associated(self):
        device = {'id': '1234abcd', 'ip': '127.0.0.1'}
        line = {'id': 1234, 'provisioning_code': "123456"}
        self.client.devices.list.return_value = {'total': 1, 'items': [device]}
        self.client.lines.list.return_value = {'total': 1, 'items': [line]}

        self.provision("123456", "127.0.0.1")

        self.client.devices.list.assert_called_once_with(ip="127.0.0.1", search="autoprov", recurse=True)
        self.client.lines.list.assert_called_once_with(provisioning_code="123456", recurse=True)
        self.client.devices.synchronize.assert_called_once_with(device['id'])

        association = self.client.lines
        associator = association.return_value

        association.assert_called_once_with(line)
        associator.add_device.assert_called_once_with(device)

    def test_given_prov_code_is_autoprov_then_device_is_reset_to_autoprov(self):
        device = {'id': '1234abcd', 'ip': '127.0.0.1'}
        self.client.devices.list.return_value = {'total': 1, 'items': [device]}

        self.provision("autoprov", "127.0.0.1")

        self.client.devices.autoprov.assert_called_once_with(device['id'])
        self.client.devices.synchronize.assert_called_once_with(device['id'])
