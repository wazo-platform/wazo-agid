# -*- coding: utf-8 -*-

__license__ = """
    Copyright (C) 2010  Avencall

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import json
from xivo_agid import agid
from xivo_agid import objects


def check_diversion(agi, cursor, args):
        queueid = agi.get_variable('XIVO_DSTID')
        try:
            queue = objects.Queue(agi, cursor, xid=int(queueid))
        except (ValueError, LookupError), e:
            agi.dp_break(str(e))

        event = 'none'
        dialaction = ''

        # . holdtime
        # set by QUEUE_VARIABLES(${XIVO_QUEUENAME})
        # NOTE: why testing waitingcalls ?
        #       once there are no more calls in queue, QUEUEHOLDTIME will NEVER be
        #       updated.
        #       Thus if we are over threshold, we can never go over.
        #       So, once queue is empty, we accept new incoming call event if holdtime
        #       is over threshold
        waitingcalls = agi.get_variable('XIVO_QUEUE_CALLS_COUNT')
        if waitingcalls == '':
            waitingcalls = 0
        if event == 'none' and int(waitingcalls) > 0 and queue.waittime is not None:
            holdtime = agi.get_variable('QUEUEHOLDTIME')
            if int(holdtime) > queue.waittime:
                event = 'DIVERT_HOLDTIME'; dialaction = 'qwaittime'

        # . calls/agents ratio
        if event == 'none' and queue.waitratio is not None:
            agents = agi.get_variable('XIVO_QUEUE_MEMBERS_COUNT')

            if int(agents) == 0 or\
                 int(waitingcalls) + 1 / int(agents) > (queue.waitratio / 100):
                event = 'DIVERT_CA_RATIO'; dialaction = 'qwaitratio'

        agi.set_variable('XIVO_DIVERT_EVENT', event)
        agi.set_variable('XIVO_FWD_TYPE'    , 'queue_' + dialaction)

agid.register(check_diversion)
