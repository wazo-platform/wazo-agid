# -*- coding: utf-8 -*-
# Copyright 2020-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import uuid

from wazo_agid import agid, dialplan_variables, objects

logger = logging.getLogger(__name__)

CALL_RECORDING_FILENAME_TEMPLATE = '/var/lib/wazo/sounds/tenants/{tenant_uuid}/monitor/{recording_uuid}.wav'


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

    user_id = agi.get_variable(dialplan_variables.USERID)
    if not user_id:
        return

    caller = objects.User(agi, cursor, int(user_id))
    if not caller:
        return

    is_external = agi.get_variable(dialplan_variables.OUTCALL_ID) != ''
    should_record = (
        (not is_external and caller.call_record_outgoing_internal_enabled)
        or (is_external and caller.call_record_outgoing_external_enabled)
    )
    if not should_record:
        return

    _start_mix_monitor(agi)


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


def start_mix_monitor(agi, cursor, args):
    _start_mix_monitor(agi)


def _start_mix_monitor(agi):
    tenant_uuid = agi.get_variable(dialplan_variables.TENANT_UUID)
    recording_uuid = str(uuid.uuid4())
    filename = CALL_RECORDING_FILENAME_TEMPLATE.format(
        tenant_uuid=tenant_uuid,
        recording_uuid=recording_uuid,
    )
    mix_monitor_options = agi.get_variable('WAZO_MIXMONITOR_OPTIONS')

    agi.appexec('MixMonitor', '{},{}'.format(filename, mix_monitor_options))
    agi.set_variable('WAZO_CALL_RECORD_ACTIVE', '1')


agid.register(call_recording)
agid.register(record_caller)
agid.register(start_mix_monitor)
