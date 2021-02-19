# -*- coding: utf-8 -*-
# Copyright 2020-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import time

from wazo_agid import agid, dialplan_variables, objects
from wazo_agid.helpers import CallRecordingNameGenerator

logger = logging.getLogger(__name__)


def call_recording(agi, cursor, args):
    calld = agi.config['calld']['client']
    channel_id = agi.env['agi_uniqueid']
    if agi.get_variable('WAZO_CALL_RECORD_ACTIVE') == '1':
        _disable_call_recording(agi, calld, channel_id)
    else:
        _enable_call_recording(agi, calld, channel_id)


def record_caller(agi, cursor, args):
    is_being_recorded = agi.get_variable('WAZO_CALL_RECORD_ACTIVE') == '1'
    if is_being_recorded:
        return

    args = {
        'srcnum': agi.get_variable(dialplan_variables.SOURCE_NUMBER),
        'dstnum': agi.get_variable('XIVO_REAL_NUMBER'),
        'timestamp': int(time.time()),
        'local_time': time.asctime(time.localtime()),
        'utc_time': time.asctime(time.gmtime()),
        'base_context': agi.get_variable('XIVO_REAL_CONTEXT'),
        'tenant_uuid': agi.get_variable(dialplan_variables.TENANT_UUID),
        'dest_type': agi.get_variable('CONTEXT'),
        'side': 'caller',
    }
    generator = CallRecordingNameGenerator(
        agi.config['call_recording']['filename_template'],
        agi.config['call_recording']['filename_extension'],
    )
    filename = generator.generate(args)
    agi.set_variable('XIVO_CALLRECORDFILE', filename)

    user_id = agi.get_variable(dialplan_variables.USERID)
    if not user_id:
        return

    caller = objects.User(agi, cursor, int(user_id))
    if not caller:
        return

    should_record = caller and caller.call_record_outgoing_internal_enabled
    if not should_record:
        return

    agi.appexec('MixMonitor', filename)
    agi.set_variable('WAZO_CALL_RECORD_ACTIVE', '1')


def _enable_call_recording(agi, calld, channel_id):
    try:
        calld.calls.start_record(channel_id)
    except Exception as e:
        logger.error('Error during enabling call recording: %s', e)


def _disable_call_recording(agi, calld, channel_id):
    try:
        calld.calls.stop_record(channel_id)
    except Exception as e:
        logger.error('Error during disabling call recording: %s', e)


agid.register(call_recording)
agid.register(record_caller)
