# Copyright 2020-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from wazo_agid import agid
from wazo_agid import dialplan_variables as dv
from wazo_agid import objects

if TYPE_CHECKING:
    from psycopg2.extras import DictCursor

    from wazo_agid.agid import FastAGI


logger = logging.getLogger(__name__)

# The recording file name template must be kept synced with RECORDING_PATH_REGEX
# in wazo-call-logd
CALL_RECORDING_FILENAME_TEMPLATE = (
    '/var/lib/wazo/sounds/tenants/{tenant_uuid}/monitor/{recording_uuid}.wav'
)


def call_recording(agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
    calld = agi.config['calld']['client']
    channel_id = agi.env['agi_uniqueid']
    tenant_uuid = agi.get_variable('WAZO_TENANT_UUID')
    if agi.get_variable('WAZO_CALL_RECORD_ACTIVE') == '1':
        if agi.get_variable('WAZO_RECORDING_PAUSED') == '1':
            _resume_call_recording(agi, calld, channel_id, tenant_uuid)
        else:
            _pause_call_recording(agi, calld, channel_id, tenant_uuid)
    else:
        _enable_call_recording(agi, calld, channel_id, tenant_uuid)


def record_caller(agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
    is_being_recorded = agi.get_variable('WAZO_CALL_RECORD_ACTIVE') == '1'
    if is_being_recorded:
        return

    argument: dict[str, str | int] = {}
    user_uuid = agi.get_variable(dv.USERUUID)
    if user_uuid:
        argument['xid'] = user_uuid
    else:
        user_id = agi.get_variable(dv.USERID)
        if not user_id:
            return
        argument['xid'] = int(user_id)

    caller = objects.User(agi, cursor, **argument)
    if not caller:
        return

    is_external = agi.get_variable(dv.OUTCALL_ID) != ''
    should_record = (
        not is_external and caller.call_record_outgoing_internal_enabled
    ) or (is_external and caller.call_record_outgoing_external_enabled)
    if not should_record:
        return

    _start_mix_monitor(agi)


def _enable_call_recording(agi, calld, channel_id, tenant_uuid):
    try:
        calld.calls.start_record(channel_id, tenant_uuid=tenant_uuid)
    except Exception as e:
        logger.error('Error during enabling call recording: %s', e)
        agi.verbose(f'Could not enable call recording: {e}')


def _pause_call_recording(agi, calld, channel_id, tenant_uuid):
    try:
        calld.calls.pause_record(channel_id, tenant_uuid=tenant_uuid)
    except Exception as e:
        logger.error('Error during pausing call recording: %s', e)
        agi.verbose(f'Could not pause call recording: {e}')


def _resume_call_recording(agi, calld, channel_id, tenant_uuid):
    try:
        calld.calls.resume_record(channel_id, tenant_uuid=tenant_uuid)
    except Exception as e:
        logger.error('Error during resume call recording: %s', e)
        agi.verbose(f'Could not resume call recording: {e}')


def start_mix_monitor(agi, cursor, args):
    _start_mix_monitor(agi)


def _start_mix_monitor(agi):
    tenant_uuid = agi.get_variable(dv.TENANT_UUID)
    recording_uuid = str(uuid.uuid4())
    filename = CALL_RECORDING_FILENAME_TEMPLATE.format(
        tenant_uuid=tenant_uuid,
        recording_uuid=recording_uuid,
    )
    mix_monitor_options: str = agi.get_variable('WAZO_MIXMONITOR_OPTIONS')
    if 'p(' in mix_monitor_options:
        p_position = mix_monitor_options.index('p(')
        ending_paren_position = mix_monitor_options.index(')')
        pre_p = mix_monitor_options[:p_position]
        post_p = mix_monitor_options[ending_paren_position + 1 :]
        mix_monitor_options = pre_p + post_p

    agi.appexec('MixMonitor', f'{filename},{mix_monitor_options}')
    agi.set_variable('WAZO_RECORDING_UUID', recording_uuid)
    agi.set_variable('WAZO_CALL_RECORD_ACTIVE', '1')


agid.register(call_recording)
agid.register(record_caller)
agid.register(start_mix_monitor)
