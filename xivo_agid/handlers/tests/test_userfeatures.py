# -*- coding: utf-8 -*-
# Copyright 2013-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import unittest
from hamcrest import assert_that
from hamcrest import contains
from hamcrest import equal_to

from mock import Mock, call, patch, sentinel

from xivo_agid.handlers.userfeatures import UserFeatures
from xivo_agid import objects

ABCD_INTERFACE = 'PJSIP/ycetqvtr/sip:n753iqfr@127.0.0.1:44530;transport=ws&PJSIP/ycetqvtr/sip:b6405ov4@127.0.0.1:44396;transport=ws'


class NotEmptyStringMatcher(object):
    def __eq__(self, other):
        return isinstance(other, basestring) and bool(other)


class _BaseTestCase(unittest.TestCase):

    def setUp(self):
        config = {'call_recording': {'filename_template': '{{ mock }}',
                                     'filename_extension': 'wav'}}
        self._agi = Mock(config=config)
        self._cursor = Mock(cast=lambda x, y: '')
        self._args = Mock()


class TestUserFeatures(_BaseTestCase):

    def setUp(self):
        super(TestUserFeatures, self).setUp()
        self._variables = {
            'PJSIP_DIAL_CONTACTS(abcd)': ABCD_INTERFACE,
            'PJSIP_DIAL_CONTACTS(foobar)': '',
            'XIVO_USERID': '42',
            'XIVO_DSTID': '33',
            'XIVO_CALLORIGIN': 'my_origin',
            'XIVO_SRCNUM': '1000',
            'XIVO_DSTNUM': '1003',
            'XIVO_DST_EXTEN_ID': '983274',
            'XIVO_BASE_CONTEXT': 'default',
        }

        def get_variable(key):
            return self._variables[key]

        self._agi.get_variable = get_variable

    def test_userfeatures(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        self.assertEqual(userfeatures._agi, self._agi)
        self.assertEqual(userfeatures._cursor, self._cursor)
        self.assertEqual(userfeatures._args, self._args)

    def test_set_members(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        userfeatures._set_caller = Mock()
        userfeatures._set_line = Mock()
        userfeatures._set_user = Mock()

        userfeatures._set_members()

        old_user, objects.User = objects.User, Mock()

        self.assertEqual(userfeatures._userid, self._variables['XIVO_USERID'])
        self.assertEqual(userfeatures._dstid, self._variables['XIVO_DSTID'])
        self.assertEqual(userfeatures._zone, self._variables['XIVO_CALLORIGIN'])
        self.assertEqual(userfeatures._srcnum, self._variables['XIVO_SRCNUM'])
        self.assertEqual(userfeatures._dstnum, self._variables['XIVO_DSTNUM'])
        self.assertTrue(userfeatures._set_caller.called)
        self.assertTrue(userfeatures._set_line.called)
        self.assertTrue(userfeatures._set_user.called)

        objects.User, old_user = old_user, None

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

    @patch('xivo_agid.handlers.userfeatures.context_dao')
    def test_set_call_recordfile_doesnt_raise_when_caller_is_none(self, context_dao):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        userfeatures._user = Mock()
        userfeatures._user.callrecord = True
        userfeatures._context = 'default'

        userfeatures._set_call_recordfile()

        self._agi.set_variable.assert_called_once_with('XIVO_CALLRECORDFILE',
                                                       NotEmptyStringMatcher())

    @patch('xivo_agid.handlers.userfeatures.extension_dao')
    @patch('xivo_agid.handlers.userfeatures.line_extension_dao')
    @patch('xivo_agid.handlers.userfeatures.line_dao')
    @patch('xivo_agid.handlers.userfeatures.user_line_dao')
    def test_set_line(self, user_line_dao, line_dao, line_extension_dao, extension_dao):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        userfeatures._set_line()
        self.assertEqual(userfeatures.lines, [])

        userfeatures._dstid = self._variables['XIVO_DSTID']
        user_lines = [Mock(user_id=1, line_id=10)]
        line = Mock(main_line=True)
        extension = Mock(exten='1234')

        user_line_dao.find_all_by.return_value = user_lines
        line_dao.find_by.return_value = line
        line_extension_dao.find_all_by.return_value = [Mock(extension_id=100)]
        extension_dao.get_by.return_value = extension

        userfeatures._set_line()

        self.assertEqual([line], userfeatures.lines)
        self.assertEqual(extension, userfeatures.main_extension)
        self.assertEqual(line, userfeatures.main_line)

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
        userfeatures._set_xivo_iface = Mock()
        userfeatures._set_user_filter = Mock()
        userfeatures._call_filtering = Mock()

        userfeatures.execute()

        self.assertEqual(userfeatures._set_members.call_count, 1)
        self.assertEqual(userfeatures._set_xivo_iface.call_count, 1)

    def test_build_interface_from_custom_line(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        line = Mock()
        line.protocol = 'CUSTOM'
        line.name = 'sip/abcd'

        interface = userfeatures._build_interface_from_line(line)

        self.assertEqual(interface, 'sip/abcd')

    def test_build_interface_from_sip_line_connected(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        line = Mock()
        line.protocol = 'SIP'
        line.name = 'abcd'

        interface = userfeatures._build_interface_from_line(line)

        self.assertEqual(interface, ABCD_INTERFACE)

    def test_build_interface_from_sip_line_not_connected(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        line = Mock()
        line.protocol = 'SIP'
        line.name = 'foobar'

        interface = userfeatures._build_interface_from_line(line)

        self.assertEqual(interface, 'PJSIP/foobar')

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

    def test_set_xivo_redirecting_info_line(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        userfeatures._user = Mock()
        userfeatures._user.callerid = '"Foobar"'
        userfeatures.main_extension = Mock(exten='32')
        userfeatures._dstnum = '42'

        userfeatures._set_xivo_redirecting_info()

        expected_calls = [
            call('XIVO_DST_REDIRECTING_NAME', 'Foobar'),
            call('XIVO_DST_REDIRECTING_NUM', '32'),
        ]
        self.assertEqual(self._agi.set_variable.call_args_list, expected_calls)

    def test_set_callfilter_ringseconds_zero(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        name = 'XIVO_CALLFILTER_TIMEOUT'
        value = 0

        userfeatures._set_callfilter_ringseconds('TIMEOUT', value)

        self._agi.set_variable.assert_called_once_with(name, '')

    def test_set_callfilter_ringseconds_negative(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        name = 'XIVO_CALLFILTER_TIMEOUT'
        value = -42

        userfeatures._set_callfilter_ringseconds('TIMEOUT', value)

        self._agi.set_variable.assert_called_once_with(name, '')

    def test_set_callfilter_ringseconds(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        name = 'XIVO_CALLFILTER_TIMEOUT'
        value = 1

        userfeatures._set_callfilter_ringseconds('TIMEOUT', value)

        self._agi.set_variable.assert_called_once_with(name, value)


class TestSetForwardNoAnswer(_BaseTestCase):

    def test_forward_no_answer_to_a_user_dialaction(self):
        user_features = UserFeatures(self._agi, self._cursor, self._args)
        user_features._user = Mock(objects.User, id=sentinel.userid)
        self._cursor.fetchone = Mock(return_value={
            'action': 'user',
            'actionarg1': '5',
            'actionarg2': '',
        })

        enabled = user_features._set_rna_from_dialaction()

        assert_that(enabled, equal_to(True))
        assert_that(self._agi.set_variable.call_args_list, contains(
            call('XIVO_FWD_USER_NOANSWER_ACTION', 'user'),
            call('XIVO_FWD_USER_NOANSWER_ISDA', '1'),
            call('XIVO_FWD_USER_NOANSWER_ACTIONARG1', '5'),
            call('XIVO_FWD_USER_NOANSWER_ACTIONARG2', ''),
        ))

    def test_forward_no_answer_to_a_user_from_exten_fwdrna_disabled_on_user(self):
        user_features = UserFeatures(self._agi, self._cursor, self._args)
        user_features._user = Mock(objects.User, enablerna=False)

        enabled = user_features._set_rna_from_exten()

        assert_that(enabled, equal_to(False))

    def test_forward_no_answer_to_a_user_from_exten(self):
        user_features = UserFeatures(self._agi, self._cursor, self._args)
        user_features._user = Mock(objects.User, destrna='555', enablerna=True)
        user_features.main_extension = Mock(context=sentinel.context)

        enabled = user_features._set_rna_from_exten()

        assert_that(enabled, equal_to(True))
        assert_that(self._agi.set_variable.call_args_list, contains(
            call('XIVO_FWD_USER_NOANSWER_ACTION', 'extension'),
            call('XIVO_FWD_USER_NOANSWER_ACTIONARG1', '555'),
            call('XIVO_FWD_USER_NOANSWER_ACTIONARG2', sentinel.context),
        ))

    def test_setrna_exten_disabled_noanswer_enabled(self):
        user_features = UserFeatures(self._agi, self._cursor, self._args)
        user_features._set_rna_from_exten = Mock(return_value=False)
        user_features._set_rna_from_dialaction = Mock(return_value=True)

        user_features._setrna()

        user_features._set_rna_from_exten.assert_called_once_with()
        assert_that(self._agi.set_variable.called_once_with('XIVO_ENABLERNA', True))

    def test_setrna_exten_disabled_noanswer_disabled(self):
        user_features = UserFeatures(self._agi, self._cursor, self._args)
        user_features._set_rna_from_exten = Mock(return_value=False)
        user_features._set_rna_from_dialaction = Mock(return_value=False)

        user_features._setrna()

        user_features._set_rna_from_exten.assert_called_once_with()
        user_features._set_rna_from_dialaction.assert_called_once_with()

        assert_that(self._agi.set_variable.call_count, equal_to(0))


class TestSetForwardBusy(_BaseTestCase):

    def test_forward_busy_to_a_user_dialaction(self):
        user_features = UserFeatures(self._agi, self._cursor, self._args)
        user_features._user = Mock(objects.User, id=sentinel.userid)
        self._cursor.fetchone = Mock(return_value={
            'action': 'user',
            'actionarg1': '5',
            'actionarg2': '',
        })

        enabled = user_features._set_rbusy_from_dialaction()

        assert_that(enabled, equal_to(True))
        assert_that(self._agi.set_variable.call_args_list, contains(
            call('XIVO_FWD_USER_BUSY_ACTION', 'user'),
            call('XIVO_FWD_USER_BUSY_ISDA', '1'),
            call('XIVO_FWD_USER_BUSY_ACTIONARG1', '5'),
            call('XIVO_FWD_USER_BUSY_ACTIONARG2', ''),
        ))

    def test_forward_busy_to_a_user_from_exten_fwdbusy_disabled_on_user(self):
        user_features = UserFeatures(self._agi, self._cursor, self._args)
        user_features._user = Mock(objects.User, enablebusy=False)

        enabled = user_features._set_rbusy_from_exten()

        assert_that(enabled, equal_to(False))

    def test_forward_busy_to_a_user_from_exten(self):
        user_features = UserFeatures(self._agi, self._cursor, self._args)
        user_features._user = Mock(objects.User, destbusy='666', enablebusy=True)
        user_features.main_extension = Mock(context=sentinel.context)

        enabled = user_features._set_rbusy_from_exten()

        assert_that(enabled, equal_to(True))
        assert_that(self._agi.set_variable.call_args_list, contains(
            call('XIVO_FWD_USER_BUSY_ACTION', 'extension'),
            call('XIVO_FWD_USER_BUSY_ACTIONARG1', '666'),
            call('XIVO_FWD_USER_BUSY_ACTIONARG2', sentinel.context),
        ))

    def test_set_rbusy_exten_disabled_noanswer_enabled(self):
        user_features = UserFeatures(self._agi, self._cursor, self._args)
        user_features._set_rbusy_from_exten = Mock(return_value=False)
        user_features._set_rbusy_from_dialaction = Mock(return_value=True)

        user_features._setbusy()

        user_features._set_rbusy_from_exten.assert_called_once_with()
        assert_that(self._agi.set_variable.called_once_with('XIVO_ENABLEBUSY', True))

    def test_set_busy_exten_disabled_noanswer_disabled(self):
        user_features = UserFeatures(self._agi, self._cursor, self._args)
        user_features._set_rbusy_from_exten = Mock(return_value=False)
        user_features._set_rbusy_from_dialaction = Mock(return_value=False)

        user_features._setbusy()

        user_features._set_rbusy_from_exten.assert_called_once_with()
        user_features._set_rbusy_from_dialaction.assert_called_once_with()

        assert_that(self._agi.set_variable.call_count, equal_to(0))
