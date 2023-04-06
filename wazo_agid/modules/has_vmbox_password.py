# Copyright 2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

from wazo_agid import agid, objects

if TYPE_CHECKING:
    from wazo_agid.agid import FastAGI
    from psycopg2.extras import DictCursor


def has_vmbox_password(agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
    userid = agi.get_variable('XIVO_USERID')

    xlen = len(args)
    user: objects.User
    if xlen > 0 and args[0] != '':
        try:
            context = agi.get_variable('XIVO_BASE_CONTEXT')
            if not context:
                agi.dp_break('Could not get the context of the caller')

            user = objects.User(agi, cursor, exten=args[0], context=context)
        except (ValueError, LookupError) as e:
            agi.dp_break(str(e))
    else:
        try:
            user = objects.User(agi, cursor, int(userid))
        except (ValueError, LookupError) as e:
            agi.dp_break(str(e))

    if not user.vmbox:
        agi.dp_break(f"User has no voicemail box (id: {user.id:d})")

    agi.set_variable('WAZO_VM_HAS_PASSWORD', 'True' if user.vmbox.password else 'False')


agid.register(has_vmbox_password)
