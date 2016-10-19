# -*- coding: utf-8 -*-

# Copyright (C) 2012-2014 Avencall
# Copyright (C) 2016 Proformatique Inc.
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
from xivo_agid.handlers.groupfeatures import GroupFeatures
from mock import Mock, patch, call


class TestGroupFeatures(unittest.TestCase):

    def setUp(self):
        self._agi = Mock()
        self._cursor = Mock()
        self._args = Mock()
        self.group_features = GroupFeatures(self._agi, self._cursor, self._args)

    @patch('xivo_agid.handlers.groupfeatures.GroupFeatures._set_members')
    @patch('xivo_agid.handlers.groupfeatures.GroupFeatures._set_options')
    @patch('xivo_agid.handlers.groupfeatures.GroupFeatures._set_vars')
    @patch('xivo_agid.handlers.groupfeatures.GroupFeatures._set_preprocess_subroutine')
    @patch('xivo_agid.handlers.groupfeatures.GroupFeatures._set_timeout')
    @patch('xivo_agid.handlers.groupfeatures.GroupFeatures._set_dial_action')
    @patch('xivo_agid.handlers.groupfeatures.GroupFeatures._set_schedule')
    @patch('xivo_agid.handlers.groupfeatures.GroupFeatures._needs_rewrite_cid')
    @patch('xivo_agid.handlers.groupfeatures.GroupFeatures._set_rewrite_cid')
    def test_execute(self,
                     _set_rewrite_cid,
                     _needs_rewrite_cid,
                     _set_schedule,
                     _set_dial_action,
                     _set_timeout,
                     _set_preprocess_subroutine,
                     _set_vars,
                     _set_options,
                     _set_members):
        _needs_rewrite_cid.return_value = True

        self.group_features.execute()

        _set_members.assert_called_once_with()
        _set_options.assert_called_once_with()
        _set_vars.assert_called_once_with()
        _set_preprocess_subroutine.assert_called_once_with()
        _set_timeout.assert_called_once_with()
        _set_dial_action.assert_called_once_with()
        _set_schedule.assert_called_once_with()
        _set_rewrite_cid.assert_called_once_with()

    def test_referer_myself_needs_rewrite_cid(self):
        self.group_features._id = 3
        self.group_features._referer = "group:3"

        self.assertTrue(self.group_features._needs_rewrite_cid())

    def test_set_schedule(self):
        self.group_features._id = 34
        self._agi.get_variable.return_value = ''

        calls = [call('XIVO_PATH', 'group'), call('XIVO_PATH_ID', 34)]

        self.group_features._set_schedule()

        self._agi.set_variable.assert_has_calls(calls)

        self._agi.set_variable.assert_any_call('XIVO_PATH', 'group')
        self._agi.set_variable.assert_any_call('XIVO_PATH_ID', 34)
