# -*- coding: utf-8 -*-
# Copyright (C) 2006-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

from xivo_agid import agid
from xivo_agid import objects


def user_get_vmbox(agi, cursor, args):
    userid = agi.get_variable('XIVO_USERID')

    xlen = len(args)

    if xlen > 0 and args[0] != '':
        try:
            context = agi.get_variable('XIVO_BASE_CONTEXT')
            if not context:
                agi.dp_break('Could not get the context of the caller')

            user = objects.User(agi, cursor, exten=args[0], context=context)
        except (ValueError, LookupError), e:
            agi.dp_break(str(e))
    else:
        try:
            user = objects.User(agi, cursor, int(userid))
        except (ValueError, LookupError), e:
            agi.dp_break(str(e))

    if not user.vmbox:
        agi.dp_break("User has no voicemail box (id: %d)" % user.id)

    if user.vmbox.skipcheckpass:
        vmmain_options = "s"
    else:
        vmmain_options = ""

    agi.set_variable('XIVO_VMMAIN_OPTIONS', vmmain_options)
    agi.set_variable('XIVO_MAILBOX', user.vmbox.mailbox)
    agi.set_variable('XIVO_MAILBOX_CONTEXT', user.vmbox.context)

agid.register(user_get_vmbox)
