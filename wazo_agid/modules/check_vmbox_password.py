# Copyright 2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

from wazo_agid import agid, objects

if TYPE_CHECKING:
    from psycopg2.extras import DictCursor

    from wazo_agid.agid import FastAGI


def check_vmbox_password(agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
    try:
        mailbox = args[0]
    except IndexError:
        agi.dp_break('check_vm_password requires a voicemail number')

    try:
        context = args[1]
    except IndexError:
        agi.dp_break('check_vm_password requires a voicemail context')

    try:
        vmbox = objects.VMBox(agi, cursor, mailbox=mailbox, context=context)
    except (ValueError, LookupError) as e:
        agi.dp_break(f'{mailbox}@{context}: no such voicemail: {e}')

    agi.set_variable(
        'WAZO_VM_HAS_PASSWORD',
        'True' if vmbox.has_password() else 'False',
    )


agid.register(check_vmbox_password)
