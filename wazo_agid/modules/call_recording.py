# -*- coding: utf-8 -*-
# Copyright 2020 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from wazo_agid import agid

logger = logging.getLogger(__name__)


def call_recording(agi, cursor, args):
    if agi.get_variable('WAZO_CALL_RECORD_ACTIVE') == '1':
        _disable_call_recording(agi, cursor, args)
    else:
        _enable_call_recording(agi, cursor, args)


def _enable_call_recording(agi, cursor, args):
    record_filename = agi.get_variable('XIVO_CALLRECORDFILE')
    if not record_filename:
        logger.error('Could not start recording: could not determine record file')
        return

    agi.appexec('MixMonitor', record_filename)
    agi.set_variable('WAZO_CALL_RECORD_ACTIVE', '1')


def _disable_call_recording(agi, cursor, args):
    agi.appexec('StopMixMonitor')
    agi.set_variable('WAZO_CALL_RECORD_ACTIVE', '0')


agid.register(call_recording)
