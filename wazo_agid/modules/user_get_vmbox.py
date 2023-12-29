# Copyright 2006-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

from wazo_agid import agid, objects

if TYPE_CHECKING:
    from psycopg2.extras import DictCursor

    from wazo_agid.agid import FastAGI


def user_get_vmbox(agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
    userid = agi.get_variable('WAZO_USERID')

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

    if user.vmbox.skipcheckpass:
        vmmain_options = "s"
    else:
        vmmain_options = ""

    agi.set_variable('XIVO_VMMAIN_OPTIONS', vmmain_options)
    agi.set_variable('XIVO_MAILBOX', user.vmbox.mailbox)
    agi.set_variable('XIVO_MAILBOX_CONTEXT', user.vmbox.context)
    if user.vmbox.password:
        agi.set_variable('WAZO_VM_PASSWORD', user.vmbox.password)


agid.register(user_get_vmbox)
