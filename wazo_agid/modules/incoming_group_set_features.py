# -*- coding: utf-8 -*-
# Copyright 2006-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_agid import agid
from wazo_agid.handlers.groupfeatures import GroupFeatures


def incoming_group_set_features(agi, cursor, args):
    groupfeatures_handler = GroupFeatures(agi, cursor, args)
    groupfeatures_handler.execute()


agid.register(incoming_group_set_features)
