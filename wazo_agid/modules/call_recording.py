# -*- coding: utf-8 -*-
# Copyright 2020-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from wazo_agid import agid

logger = logging.getLogger(__name__)


def call_recording(agi, cursor, args):
    calld = agi.config['calld']['client']
    channel_id = agi.env['agi_uniqueid']
    if agi.get_variable('WAZO_CALL_RECORD_ACTIVE') == '1':
        _disable_call_recording(agi, calld, channel_id)
    else:
        _enable_call_recording(agi, calld, channel_id)


def _enable_call_recording(agi, calld, channel_id):
    record_filename = agi.get_variable('XIVO_CALLRECORDFILE')
    if not record_filename:
        logger.error('Could not start recording: could not determine record file')
        return

    try:
        calld.calls.start_record(channel_id)
    except Exception as e:
        logger.error('Error during enabling call recording: %s', e)

    agi.set_variable('WAZO_CALL_RECORD_ACTIVE', '1')


def _disable_call_recording(agi, calld, channel_id):
    try:
        calld.calls.stop_record(channel_id)
    except Exception as e:
        logger.error('Error during disabling call recording: %s', e)

    agi.set_variable('WAZO_CALL_RECORD_ACTIVE', '0')


agid.register(call_recording)
