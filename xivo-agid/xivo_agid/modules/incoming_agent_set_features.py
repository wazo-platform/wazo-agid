# -*- coding: UTF-8 -*-

__license__ = """
    Copyright (C) 2013  Avencall

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


def incoming_agent_set_features(agi, cursor, args):
    try:
        agent_id = args[0]
    except IndexError:
        agi.dp_break('Missing feature agent_id argument')
    try:
        device = agent.get_agent_device(agi, agent_id, cursor)
    except LookupError as e:
        agi.dp_break(str(e))
    agi.set_variable('XIVO_AGENT_INTERFACE', device)


agid.register(incoming_agent_set_features)
