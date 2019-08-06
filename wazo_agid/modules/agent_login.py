# -*- coding: utf-8 -*-
# Copyright 2012-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from xivo_agid import agid
from xivo_agid.handlers import agent

logger = logging.getLogger(__name__)


def agent_login(agi, cursor, args):
    try:
        tenant_uuid = args[0]
        agent_id = int(args[1])
        extension = args[2]
        context = args[3]

        agent.login_agent(agi, agent_id, extension, context, tenant_uuid)
    except Exception as e:
        logger.exception("Error while logging in agent")
        agi.dp_break(e)


agid.register(agent_login)
