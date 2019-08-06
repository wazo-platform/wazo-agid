# -*- coding: utf-8 -*-
# Copyright 2006-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_agid import agid
from wazo_agid.handlers.userfeatures import UserFeatures


def incoming_user_set_features(agi, cursor, args):
    userfeatures_handler = UserFeatures(agi, cursor, args)
    userfeatures_handler.execute()


agid.register(incoming_user_set_features)
