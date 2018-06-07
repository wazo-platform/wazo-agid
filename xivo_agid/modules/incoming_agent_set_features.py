# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

from xivo_agid import agid
from xivo_agid.handlers.agentfeatures import AgentFeatures


def incoming_agent_set_features(agi, cursor, args):
    agentfeatures_handler = AgentFeatures(agi, cursor, args)
    agentfeatures_handler.execute()

agid.register(incoming_agent_set_features)
