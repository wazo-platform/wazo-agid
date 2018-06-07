# -*- coding: utf-8 -*-
# Copyright (C) 2006-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

from xivo_agid import agid
from xivo_agid.handlers.groupfeatures import GroupFeatures


def incoming_group_set_features(agi, cursor, args):
    groupfeatures_handler = GroupFeatures(agi, cursor, args)
    groupfeatures_handler.execute()

agid.register(incoming_group_set_features)
