# -*- coding: utf-8 -*-
# Copyright (C) 2008-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

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
