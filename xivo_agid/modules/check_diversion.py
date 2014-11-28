# -*- coding: utf-8 -*-

# Copyright (C) 2010-2014 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from xivo_agid import agid
from xivo_agid import objects


def check_diversion(agi, cursor, args):
    queueid = agi.get_variable('XIVO_DSTID')
    try:
        queue = objects.Queue(agi, cursor, xid=int(queueid))
    except (ValueError, LookupError), e:
        agi.dp_break(str(e))

    waiting_calls = int(agi.get_variable('QUEUE_WAITING_COUNT({})'.format(queue.name)))
    if _is_hold_time_overrun(agi, queue, waiting_calls):
        _set_diversion(agi, 'DIVERT_HOLDTIME', 'qwaittime')
    elif _is_agent_ratio_overrun(agi, queue, waiting_calls):
        _set_diversion(agi, 'DIVERT_CA_RATIO', 'qwaitratio')


def _is_hold_time_overrun(agi, queue, waiting_calls):
    if queue.waittime is None or waiting_calls == 0:
        return False

    holdtime = int(agi.get_variable('QUEUEHOLDTIME'))
    return holdtime > queue.waittime


def _is_agent_ratio_overrun(agi, queue, waiting_calls):
    if queue.waitratio is None:
        return False

    agents = int(agi.get_variable('QUEUE_MEMBER({},logged)'.format(queue.name)))
    if agents == 0:
        return True

    return (waiting_calls + 1.0) / agents > queue.waitratio


def _set_diversion(agi, event, dialaction):
    agi.set_variable('XIVO_DIVERT_EVENT', event)
    agi.set_variable('XIVO_FWD_TYPE', 'queue_' + dialaction)


agid.register(check_diversion)
