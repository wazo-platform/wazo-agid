# -*- coding: utf-8 -*-
# Copyright 2012-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from wazo_agid.handlers.groupfeatures import GroupFeatures
from mock import Mock, patch, call


class TestGroupFeatures(unittest.TestCase):

    def setUp(self):
        config = {
            'call_recording': {
                'filename_template': '{{ mock }}',
                'filename_extension': 'wav',
            },
        }
        self._agi = Mock(config=config)
        self._cursor = Mock()
        self._args = Mock()
        self.group_features = GroupFeatures(self._agi, self._cursor, self._args)
        self.call_recording_name_generator = Mock()
        self.group_features._call_recording_name_generator = self.call_recording_name_generator

    @patch('wazo_agid.handlers.groupfeatures.GroupFeatures._set_members')
    @patch('wazo_agid.handlers.groupfeatures.GroupFeatures._set_options')
    @patch('wazo_agid.handlers.groupfeatures.GroupFeatures._set_vars')
    @patch('wazo_agid.handlers.groupfeatures.GroupFeatures._set_preprocess_subroutine')
    @patch('wazo_agid.handlers.groupfeatures.GroupFeatures._set_timeout')
    @patch('wazo_agid.handlers.groupfeatures.GroupFeatures._set_dial_action')
    @patch('wazo_agid.handlers.groupfeatures.GroupFeatures._set_schedule')
    @patch('wazo_agid.handlers.groupfeatures.GroupFeatures._needs_rewrite_cid')
    @patch('wazo_agid.handlers.groupfeatures.GroupFeatures._set_rewrite_cid')
    @patch('wazo_agid.handlers.groupfeatures.GroupFeatures._set_call_record_filename')
    def test_execute(self,
                     _set_rewrite_cid,
                     _needs_rewrite_cid,
                     _set_schedule,
                     _set_dial_action,
                     _set_timeout,
                     _set_preprocess_subroutine,
                     _set_vars,
                     _set_options,
                     _set_members,
                     _set_call_record_filename):
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
        _set_call_record_filename.assert_called_once_with()

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

    def test_call_record_filename(self):
        self._agi.get_variable.side_effect = {
            'WAZO_TENANT_UUID': '190849e0-e7dc-494d-a26d-034aa37b98c4',
        }.get
        filename = '/foo/bar.wav'
        self.call_recording_name_generator.generate.return_value = filename

        self.group_features._set_call_record_filename()

        self._agi.set_variable.assert_called_once_with('__XIVO_CALLRECORDFILE', filename)
