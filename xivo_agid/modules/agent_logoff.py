# -*- coding: utf-8 -*-
# Copyright (C) 2012-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

import logging
from xivo_agid import agid
from xivo_agid.handlers import agent

logger = logging.getLogger(__name__)


def agent_logoff(agi, cursor, args):
    try:
        agent_id = int(args[0])

        agent.logoff_agent(agi, agent_id)
    except Exception as e:
        logger.exception("Error while logging off agent")
        agi.dp_break(e)


agid.register(agent_logoff)
