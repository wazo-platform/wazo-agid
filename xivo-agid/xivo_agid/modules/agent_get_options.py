# -*- coding: utf-8 -*-

# Copyright (C) 2008-2013 Avencall
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

import logging
from xivo_agid import agid
from xivo_agid import objects

logger = logging.getLogger(__name__)


def agent_get_options(agi, cursor, args):
    agi.set_variable('XIVO_AGENTEXISTS', 0)

    try:
        number = str(args[0])

        if number.startswith('*'):
            agent = objects.Agent(agi, cursor, xid=number[1:])
        else:
            agent = objects.Agent(agi, cursor, number=number)
    except (LookupError, IndexError) as e:
        agi.verbose(str(e))
        return

    agi.set_variable('XIVO_AGENTEXISTS', 1)
    agi.set_variable('XIVO_AGENTPASSWD', agent.passwd)
    agi.set_variable('XIVO_AGENTID', agent.id)
    agi.set_variable('XIVO_AGENTNUM', agent.number)

    if agent.language:
        agi.set_variable('CHANNEL(language)', agent.language)


agid.register(agent_get_options)
