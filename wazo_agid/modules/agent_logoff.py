# Copyright 2012-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from wazo_agid import agid
from wazo_agid.handlers import agent

if TYPE_CHECKING:
    from wazo_agid.agid import FastAGI
    from psycopg2.extras import DictCursor

logger = logging.getLogger(__name__)


def agent_logoff(agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
    try:
        tenant_uuid = args[0]
        agent_id = int(args[1])

        agent.logoff_agent(agi, agent_id, tenant_uuid=tenant_uuid)
    except Exception as e:
        logger.exception("Error while logging off agent")
        agi.dp_break(e)


agid.register(agent_logoff)
