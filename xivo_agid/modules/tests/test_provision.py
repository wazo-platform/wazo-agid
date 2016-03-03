# -*- coding: UTF-8 -*-

# Copyright (C) 2016 Avencall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import unittest

from mock import patch

from xivo_agid.modules import provision


@patch('xivo_agid.modules.provision.Client')
class TestDoProvision(unittest.TestCase):

    EMPTY_LIST = {'total': 0, 'items': []}

    def test_given_device_does_not_exist_when_provisioning_then_raises_error(self, client):
        client.return_value.devices.list.return_value = self.EMPTY_LIST

        self.assertRaises(Exception, provision._do_provision, "123456", "127.0.0.1")

    def test_given_line_does_not_exist_when_provisioning_then_raises_error(self, client):
        device = {'id': '1234abcd', 'ip': '127.0.0.1'}
        client.return_value.devices.list.return_value = {'total': 1, 'items': [device]}
        client.return_value.lines.list.return_value = self.EMPTY_LIST

        self.assertRaises(Exception, provision._do_provision, "123456", "127.0.0.1")

    def test_given_line_and_device_exist_when_provisioning_then_line_and_device_associated(self, client):
        device = {'id': '1234abcd', 'ip': '127.0.0.1'}
        line = {'id': 1234, 'provisioning_code': "123456"}
        client.return_value.devices.list.return_value = {'total': 1, 'items': [device]}
        client.return_value.lines.list.return_value = {'total': 1, 'items': [line]}

        provision._do_provision("123456", "127.0.0.1")

        client.return_value.devices.list.assert_called_once_with(ip="127.0.0.1")
        client.return_value.lines.list.assert_called_once_with(provisioning_code="123456")
        client.return_value.devices.synchronize.assert_called_once_with(device['id'])

        association = client.return_value.lines
        associator = association.return_value

        association.assert_called_once_with(line)
        associator.add_device.assert_called_once_with(device)
