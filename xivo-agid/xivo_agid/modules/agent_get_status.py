# -*- coding: UTF-8 -*-

__license__ = """
    Copyright (C) 2012  Avencall

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

import logging
from xivo_agid import agid
from xivo_agid.handlers import agent

logger = logging.getLogger(__name__)


def agent_get_status(agi, cursor, args):
    try:
        agent_id = int(args[0])

        agent.get_agent_status(agi, agent_id)
    except Exception as e:
        logger.exception("Error while logging off agent")
        agi.dp_break(e)


agid.register(agent_get_status)
