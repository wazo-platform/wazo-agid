# -*- coding: utf-8 -*-

# XiVO CTI Server
# Copyright (C) 2009-2012  Avencall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Alternatively, XiVO CTI Server is available under other licenses directly
# contracted with Pro-formatique SARL. See the LICENSE file at top of the
# source tree or delivered in the installable package in which XiVO CTI Server
# is distributed for more details.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from mock import Mock
from xivo_cti.directory.data_sources.ldap import LDAPDirectoryDataSource

class TestLDAPDirectoryDataSource(unittest.TestCase):
    def setUp(self):
        self._ldap = LDAPDirectoryDataSource(None, None)

    def test_decode_results(self):
        ldap_results = [('dn=someóne,dn=somewhere', {'cn': ['anó nymous'],
                                                     'sn': ['nymous']}),
                        ('dn=somebódy,dn=someplace', {'cn': ['jóhn doe'],
                                                      'sn': ['dóe']})]
        expected_result = [(u'dn=someóne,dn=somewhere', {u'cn': [u'anó nymous'],
                                                         u'sn': [u'nymous']}),
                           (u'dn=somebódy,dn=someplace', {u'cn': [u'jóhn doe'],
                                                          u'sn': [u'dóe']})]
        decode_entry = Mock()
        returns = iter(expected_result)
        decode_entry.side_effect = lambda index: returns.next()
        self._ldap._decode_entry = decode_entry

        result = self._ldap._decode_results(ldap_results)

        self.assertEquals(result, expected_result)
        decode_entry.assert_was_called_with(ldap_results[0])
        decode_entry.assert_was_called_with(ldap_results[1])

    def test_decode_entry(self):
        entry = ('dn=someóne,dn=somewhere', {'cn': ['anó nymous'],
                                             'sn': ['nymous']})
        expected_result = (u'dn=someóne,dn=somewhere', {u'cn': [u'anó nymous'],
                                                        u'sn': [u'nymous']})
        decode_attributes = Mock()
        decode_attributes.return_value = expected_result[1]
        self._ldap._decode_attributes = decode_attributes

        result = self._ldap._decode_entry(entry)

        self.assertEqual(result, expected_result)
        decode_attributes.assert_called_once_with(entry[1])

    def test_decode_attributes(self):
        attributes = {'cn': ['anó nymous'],
                      'sn': ['nymous']}
        expected_result = {u'cn': [u'anó nymous'],
                           u'sn': [u'nymous']}

        decode_values = Mock()
        returns = iter(expected_result.values())
        decode_values.side_effect = lambda index: returns.next()
        self._ldap._decode_values = decode_values

        result = self._ldap._decode_attributes(attributes)

        self.assertEqual(result, expected_result)
        decode_values.assert_was_called_with(attributes['cn'])
        decode_values.assert_was_called_with(attributes['sn'])

    def test_decode_values(self):
        values = ['anó nymous']
        expected_result = [u'anó nymous']

        result = self._ldap._decode_values(values)

        self.assertEqual(result, expected_result)
