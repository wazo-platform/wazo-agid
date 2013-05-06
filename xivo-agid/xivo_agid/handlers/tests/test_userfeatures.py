# -*- coding: utf-8 -*-

# Copyright (C) 2013 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import unittest
from mock import Mock, call, patch, sentinel

from xivo_agid.handlers.userfeatures import UserFeatures
from xivo_agid import objects


class NotEmptyStringMatcher(object):
    def __eq__(self, other):
        return isinstance(other, basestring) and bool(other)


class TestUserFeatures(unittest.TestCase):

    def setUp(self):
        self._variables = {'XIVO_USERID': '42',
                           'XIVO_DSTID': '33',
                           'XIVO_LINEID': '5',
                           'XIVO_CALLORIGIN': 'my_origin',
                           'XIVO_SRCNUM': '1000',
                           'XIVO_DSTNUM': '1003', }

        def get_variable(key):
            return self._variables[key]

        self._agi = Mock()
        self._agi.get_variable = get_variable
        self._cursor = Mock()
        self._args = Mock()

    def test_userfeatures(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        self.assertEqual(userfeatures._agi, self._agi)
        self.assertEqual(userfeatures._cursor, self._cursor)
        self.assertEqual(userfeatures._args, self._args)

    def test_set_members(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        userfeatures._set_feature_list = Mock()
        userfeatures._set_caller = Mock()
        userfeatures._set_lines = Mock()
        userfeatures._set_user = Mock()

        userfeatures._set_members()

        objects.ExtenFeatures = Mock()
        old_user, objects.User = objects.User, Mock()

        self.assertEqual(userfeatures._userid, self._variables['XIVO_USERID'])
        self.assertEqual(userfeatures._dstid, self._variables['XIVO_DSTID'])
        self.assertEqual(userfeatures._lineid, int(self._variables['XIVO_LINEID']))
        self.assertEqual(userfeatures._zone, self._variables['XIVO_CALLORIGIN'])
        self.assertEqual(userfeatures._srcnum, self._variables['XIVO_SRCNUM'])
        self.assertEqual(userfeatures._dstnum, self._variables['XIVO_DSTNUM'])
        self.assertTrue(userfeatures._set_feature_list.called)
        self.assertTrue(userfeatures._set_caller.called)
        self.assertTrue(userfeatures._set_lines.called)
        self.assertTrue(userfeatures._set_user.called)

        objects.User, old_user = old_user, None

    def test_set_feature_list(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        with patch.object(objects.ExtenFeatures, '__init__') as extenfeatures_init:
            extenfeatures_init.return_value = None
            userfeatures._set_feature_list()
            extenfeatures_init.assert_called_with(self._agi, self._cursor)
        self.assertNotEqual(userfeatures._feature_list, None)
        self.assertTrue(isinstance(userfeatures._feature_list, objects.ExtenFeatures))

    def test_set_caller(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        userfeatures._set_caller()

        self.assertTrue(userfeatures._caller is None)

        userfeatures._userid = self._variables['XIVO_USERID']

        with patch.object(objects.User, '__init__') as user_init:
            user_init.return_value = None

            userfeatures._set_caller()

            user_init.assert_called_with(self._agi, self._cursor, int(self._variables['XIVO_USERID']))
        self.assertTrue(userfeatures._caller is not None)
        self.assertTrue(isinstance(userfeatures._caller, objects.User))

    def test_set_call_recordfile_doesnt_raise_when_caller_is_none(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        userfeatures._feature_list = Mock()
        userfeatures._feature_list.callrecord = True
        userfeatures._user = Mock()
        userfeatures._user.callrecord = True

        userfeatures._set_call_recordfile()

        self._agi.set_variable.assert_called_once_with('XIVO_CALLRECORDFILE',
                                                       NotEmptyStringMatcher())

    def test_set_lines(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        mocked_line = Mock()
        mocked_line.lines = [{'number': '1001'}]

        userfeatures._set_lines()

        self.assertEqual(userfeatures._lines, None)

        userfeatures._dstid = self._variables['XIVO_DSTID']
        with patch('xivo_agid.objects.Lines') as lines_cls:
            lines_cls.return_value = mocked_line

            userfeatures._set_lines()

            lines_cls.assert_called_with(self._agi, self._cursor, int(self._variables['XIVO_DSTID']))
        self.assertEqual(mocked_line, userfeatures._lines)
        self.assertEqual(mocked_line.lines[0], userfeatures._master_line)

    def test_set_called_line_no_lineid(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        userfeatures._set_called_line()

        self.assertTrue(userfeatures._called_line is None)

    def test_set_called_line_with_matching_line(self):
        line_id = 32
        line = {'id': line_id}
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        userfeatures._lineid = line_id
        userfeatures._lines = Mock()
        userfeatures._lines.lines = [{'id': line_id + 1}, line]

        userfeatures._set_called_line()

        self.assertEqual(userfeatures._called_line, line)

    def test_set_user(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        userfeatures._set_xivo_user_name = Mock()
        userfeatures._set_xivo_redirecting_info = Mock()

        userfeatures._set_user()

        self.assertTrue(userfeatures._user is None)
        self.assertEqual(userfeatures._set_xivo_user_name.call_count, 0)

        userfeatures._dstid = self._variables['XIVO_DSTID']

        with patch.object(objects.User, '__init__') as user_init:
            user_init.return_value = None

            userfeatures._set_user()

            self.assertEqual(userfeatures._set_xivo_user_name.call_count, 1)
            self.assertEqual(userfeatures._set_xivo_redirecting_info.call_count, 1)
            self.assertTrue(userfeatures._user is not None)
            self.assertTrue(isinstance(userfeatures._user, objects.User))

    def test_execute(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        userfeatures._set_members = Mock()
        userfeatures._set_xivo_ifaces = Mock()
        userfeatures._set_user_filter = Mock()
        userfeatures._call_filtering = Mock()

        userfeatures.execute()

        self.assertEqual(userfeatures._set_members.call_count, 1)
        self.assertEqual(userfeatures._set_xivo_ifaces.call_count, 1)

    def test_xivo_set_iface_nb(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        userfeatures._set_xivo_iface_nb(sentinel.number)

        self._agi.set_variable.assert_called_once_with('XIVO_INTERFACE_NB', sentinel.number)

    def test_is_main_line(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        self.assertFalse(userfeatures._is_main_line())

        lineid = '97'
        userfeatures._lineid = lineid
        userfeatures._master_line = {'id': lineid}

        self.assertTrue(userfeatures._is_main_line())

    def test_build_interface_from_custom_line(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        line = {
            'protocol': 'CUSTOM',
            'name': 'sip/abcd'
        }

        interface = userfeatures._build_interface_from_line(line)

        self.assertEqual(interface, 'sip/abcd')

    def test_build_interface_from_sip_line(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        line = {
            'protocol': 'SIP',
            'name': 'abcd'
        }

        interface = userfeatures._build_interface_from_line(line)

        self.assertEqual(interface, 'SIP/abcd')

    def test_set_xivo_user_name(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        userfeatures._set_xivo_user_name()

        self.assertEqual(self._agi.call_count, 0)

        self._agi.set_variable.reset_mock()

        userfeatures._user = Mock()
        userfeatures._user.firstname = 'firstname'
        userfeatures._user.lastname = 'lastname'

        userfeatures._set_xivo_user_name()

        self.assertEqual(self._agi.set_variable.call_count, 2)

    def test_set_xivo_redirecting_info_full_callerid(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        userfeatures._user = Mock()
        userfeatures._user.callerid = '"Foobar" <123>'
        userfeatures._dstnum = '42'

        userfeatures._set_xivo_redirecting_info()

        expected_calls = [
            call('XIVO_DST_REDIRECTING_NAME', 'Foobar'),
            call('XIVO_DST_REDIRECTING_NUM', '123'),
        ]
        self.assertEqual(self._agi.set_variable.call_args_list, expected_calls)

    def test_set_xivo_redirecting_info_no_callerid(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        userfeatures._user = Mock()
        userfeatures._user.firstname = 'First'
        userfeatures._user.lastname = 'Last'
        userfeatures._user.callerid = ''
        userfeatures._dstnum = '42'

        userfeatures._set_xivo_redirecting_info()

        expected_calls = [
            call('XIVO_DST_REDIRECTING_NAME', 'First Last'),
            call('XIVO_DST_REDIRECTING_NUM', '42'),
        ]
        self.assertEqual(self._agi.set_variable.call_args_list, expected_calls)

    def test_set_xivo_redirecting_info_called_line(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        userfeatures._user = Mock()
        userfeatures._user.callerid = '"Foobar"'
        userfeatures._called_line = {'number': '64'}
        userfeatures._master_line = {'number': '32'}
        userfeatures._dstnum = '42'

        userfeatures._set_xivo_redirecting_info()

        expected_calls = [
            call('XIVO_DST_REDIRECTING_NAME', 'Foobar'),
            call('XIVO_DST_REDIRECTING_NUM', '64'),
        ]
        self.assertEqual(self._agi.set_variable.call_args_list, expected_calls)

    def test_set_xivo_redirecting_info_master_line(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        userfeatures._user = Mock()
        userfeatures._user.callerid = '"Foobar"'
        userfeatures._master_line = {'number': '32'}
        userfeatures._dstnum = '42'

        userfeatures._set_xivo_redirecting_info()

        expected_calls = [
            call('XIVO_DST_REDIRECTING_NAME', 'Foobar'),
            call('XIVO_DST_REDIRECTING_NUM', '32'),
        ]
        self.assertEqual(self._agi.set_variable.call_args_list, expected_calls)
