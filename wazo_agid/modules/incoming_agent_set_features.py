# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_agid import agid
from wazo_agid.handlers.agentfeatures import AgentFeatures


def incoming_agent_set_features(agi, cursor, args):
    agentfeatures_handler = AgentFeatures(agi, cursor, args)
    agentfeatures_handler.execute()


agid.register(incoming_agent_set_features)
