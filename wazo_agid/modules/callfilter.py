# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

from xivo_agid import agid, dialplan_variables
from xivo_dao import callfilter_dao


def callfilter(agi, cursor, args):
    callfiltermember_id = args[0]

    if not callfiltermember_id.isdigit():
        agi.dp_break('This id "%s" is not a valid callfiltermember_id id.' % callfiltermember_id)

    caller_user_id = agi.get_variable(dialplan_variables.USERID)
    callfiltermember = callfilter_dao.get_by_callfiltermember_id(callfiltermember_id)
    if not callfiltermember:
        agi.dp_break('This callfilter does not exist.')

    bslist = callfilter_dao.get(callfiltermember.callfilterid)
    if not bslist:
        agi.dp_break('This callfilter has no member.')

    allow_ids = []
    for bs in bslist:
        callfilter, callfiltermembers = bs
        allow_ids.append(callfiltermembers.typeval)

    if not caller_user_id or caller_user_id not in allow_ids:
        agi.dp_break('This user is not allowed to use this callfilter.')

    new_state = 0 if callfiltermember.active == 1 else 1
    callfilter_dao.update_callfiltermember_state(callfiltermember_id, new_state)
    agi.set_variable('XIVO_BSFILTERENABLED', new_state)


agid.register(callfilter)
