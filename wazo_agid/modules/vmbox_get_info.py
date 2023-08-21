# Copyright 2006-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging

from psycopg2.extras import DictCursor

from wazo_agid import agid, objects

logger = logging.getLogger(__name__)


def vmbox_get_info(agi: agid.FastAGI, cursor: DictCursor, args: list[str]) -> None:
    caller: objects.User = None  # type: ignore[assignment]
    vmbox: objects.VMBox = None  # type: ignore[assignment]
    xlen = len(args)
    if xlen > 0 and args[0] != '':
        try:
            xivo_userid = agi.get_variable('XIVO_USERID')
            if xivo_userid:
                caller = objects.User(agi, cursor, xid=int(xivo_userid))
            context = agi.get_variable('XIVO_BASE_CONTEXT')
            if not context:
                agi.dp_break('Could not get the context of the caller')

            vmbox = objects.VMBox(agi, cursor, mailbox=args[0], context=context)
        except (ValueError, LookupError) as e:
            logger.error(
                'Error while retrieving vmbox from number and context', exc_info=True
            )
            agi.dp_break(str(e))
    else:
        try:
            vmboxid = int(agi.get_variable('XIVO_VMBOXID'))
            vmbox = objects.VMBox(agi, cursor, vmboxid)
        except (ValueError, LookupError) as e:
            logger.error('Error while retrieving vmbox from id', exc_info=True)
            agi.dp_break(str(e))

    if vmbox.skipcheckpass:
        vmmain_options = "s"
    else:
        vmmain_options = ""

    if caller and caller.language:
        mbox_lang = caller.language
    elif vmbox.language:
        mbox_lang = vmbox.language
    else:
        mbox_lang = ''

    agi.set_variable('XIVO_VMMAIN_OPTIONS', vmmain_options)
    agi.set_variable('XIVO_MAILBOX', vmbox.mailbox)
    agi.set_variable('XIVO_MAILBOX_CONTEXT', vmbox.context)
    agi.set_variable('XIVO_MAILBOX_LANGUAGE', mbox_lang)


agid.register(vmbox_get_info)
