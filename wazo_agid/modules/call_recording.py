# Copyright 2020-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from wazo_agid import agid, dialplan_variables, objects

if TYPE_CHECKING:
    from psycopg2.extras import DictCursor

    from wazo_agid.agid import FastAGI


logger = logging.getLogger(__name__)

CALL_RECORDING_FILENAME_TEMPLATE = (
    '/var/lib/wazo/sounds/tenants/{tenant_uuid}/monitor/{recording_uuid}.wav'
)

CALL_RECORDING_FILENAME_TEMPLATE_A = (
    '/var/lib/wazo/sounds/tenants/{tenant_uuid}/monitor/{recording_uuid}-a.wav'
)

CALL_RECORDING_FILENAME_TEMPLATE_B = (
    '/var/lib/wazo/sounds/tenants/{tenant_uuid}/monitor/{recording_uuid}-b.wav'
)


def call_recording(agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
    calld = agi.config['calld']['client']
    channel_id = agi.env['agi_uniqueid']
    if agi.get_variable('WAZO_CALL_RECORD_ACTIVE') == '1':
        _disable_call_recording(agi, calld, channel_id)
    else:
        _enable_call_recording(agi, calld, channel_id)


def setup_binaural_mixmonitor(agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
    tenant_uuid = agi.get_variable(dialplan_variables.TENANT_UUID)
    recording_uuid = str(uuid.uuid4())
    filename = CALL_RECORDING_FILENAME_TEMPLATE.format(
        tenant_uuid=tenant_uuid,
        recording_uuid=recording_uuid,
    )
    filename_a = CALL_RECORDING_FILENAME_TEMPLATE_A.format(
        tenant_uuid=tenant_uuid,
        recording_uuid=recording_uuid,
    )
    filename_b = CALL_RECORDING_FILENAME_TEMPLATE_B.format(
        tenant_uuid=tenant_uuid,
        recording_uuid=recording_uuid,
    )
    mix_monitor_options = agi.get_variable('WAZO_MIXMONITOR_OPTIONS')

    binaural_options = f'r({filename_a})t({filename_b})'
    mixmonitor_command = f'/usr/bin/sox -M -v 1 {filename_a} -v 1 {filename_b} {filename} && rm {filename_a} {filename_b}'
    new_mixmonitor_options = f'{mix_monitor_options}{binaural_options}'
    agi.set_variable('WAZO_MIXMONITOR_OPTIONS', new_mixmonitor_options)
    agi.set_variable('WAZO_MIXMONITOR_COMMAND', mixmonitor_command)


def record_caller(agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
    is_being_recorded = agi.get_variable('WAZO_CALL_RECORD_ACTIVE') == '1'
    if is_being_recorded:
        return

    argument: dict[str, str | int] = {}
    user_uuid = agi.get_variable(dialplan_variables.USERUUID)
    if user_uuid:
        argument['xid'] = user_uuid
    else:
        user_id = agi.get_variable(dialplan_variables.USERID)
        if not user_id:
            return
        argument['xid'] = int(user_id)

    caller = objects.User(agi, cursor, **argument)
    if not caller:
        return

    is_external = agi.get_variable(dialplan_variables.OUTCALL_ID) != ''
    should_record = (
        not is_external and caller.call_record_outgoing_internal_enabled
    ) or (is_external and caller.call_record_outgoing_external_enabled)
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
    filename_a = CALL_RECORDING_FILENAME_TEMPLATE_A.format(
        tenant_uuid=tenant_uuid,
        recording_uuid=recording_uuid,
    )
    filename_b = CALL_RECORDING_FILENAME_TEMPLATE_B.format(
        tenant_uuid=tenant_uuid,
        recording_uuid=recording_uuid,
    )
    mix_monitor_options = agi.get_variable('WAZO_MIXMONITOR_OPTIONS')

    agi.appexec('MixMonitor', f'{filename},{mix_monitor_options}r({filename_a})t({filename_b}),/usr/bin/sox -M -v 1 {filename_a} -v 1 {filename_b} {filename} && rm {filename_a} {filename_b}')
    agi.set_variable('WAZO_CALL_RECORD_ACTIVE', '1')


agid.register(call_recording)
agid.register(record_caller)
agid.register(start_mix_monitor)
agid.register(setup_binaural_mixmonitor)
