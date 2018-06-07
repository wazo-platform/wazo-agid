# -*- coding: utf-8 -*-
# Copyright (C) 2012-2015 Avencall
# SPDX-License-Identifier: GPL-3.0+

import logging
from xivo_agid import agid
from xivo_agid.handlers import agent

logger = logging.getLogger(__name__)


def agent_get_status(agi, cursor, args):
    try:
        agent_id = int(args[0])

        agent.get_agent_status(agi, agent_id)
    except Exception as e:
        logger.exception("Error while getting agent status")
        agi.dp_break(e)


agid.register(agent_get_status)
