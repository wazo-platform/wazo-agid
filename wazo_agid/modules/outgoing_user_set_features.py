# -*- coding: utf-8 -*-
# Copyright 2006-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_agid.handlers.outgoingfeatures import OutgoingFeatures
from wazo_agid import agid


def outgoing_user_set_features(agi, cursor, args):
    outgoing_features_handler = OutgoingFeatures(agi, cursor, args)
    outgoing_features_handler.execute()


agid.register(outgoing_user_set_features)
