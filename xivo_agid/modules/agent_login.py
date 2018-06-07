# -*- coding: utf-8 -*-
# Copyright (C) 2012-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

import logging
from xivo_agid import agid
from xivo_agid.handlers import agent

logger = logging.getLogger(__name__)


def agent_login(agi, cursor, args):
    try:
        agent_id = int(args[0])
        extension = args[1]
        context = args[2]

        agent.login_agent(agi, agent_id, extension, context)
    except Exception as e:
        logger.exception("Error while logging in agent")
        agi.dp_break(e)


agid.register(agent_login)
