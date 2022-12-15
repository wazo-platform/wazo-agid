# Copyright 2012-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from wazo_agid import agid
from wazo_agid.handlers import agent

logger = logging.getLogger(__name__)


def agent_get_status(agi, cursor, args):
    try:
        tenant_uuid = args[0]
        agent_id = int(args[1])

        agent.get_agent_status(agi, agent_id, tenant_uuid=tenant_uuid)
    except Exception as e:
        logger.exception("Error while getting agent status")
        agi.dp_break(e)


agid.register(agent_get_status)
