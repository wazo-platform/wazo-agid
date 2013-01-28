# -*- coding: utf-8 -*-
#
# Copyright (C) 2013  Avencall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Alternatively, XiVO CTI Server is available under other licenses directly
# contracted with Avencall. See the LICENSE file at top of the source tree
# or delivered in the installable package in which XiVO CTI Server is
# distributed for more details.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from xivo_agid import agid, dialplan_variables
from xivo_dao import callfilter_dao


def callfilter(agi, cursor, args):
    callfiltermember_id = args[0]
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
