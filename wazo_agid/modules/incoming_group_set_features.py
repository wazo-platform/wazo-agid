# -*- coding: utf-8 -*-
# Copyright 2006-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from xivo_agid import agid
from xivo_agid.handlers.groupfeatures import GroupFeatures


def incoming_group_set_features(agi, cursor, args):
    groupfeatures_handler = GroupFeatures(agi, cursor, args)
    groupfeatures_handler.execute()


agid.register(incoming_group_set_features)
