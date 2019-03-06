# -*- coding: utf-8 -*-
# Copyright (C) 2006-2014 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

from xivo_agid.handlers.outgoingfeatures import OutgoingFeatures
from xivo_agid import agid


def outgoing_user_set_features(agi, cursor, args):
    outgoing_features_handler = OutgoingFeatures(agi, cursor, args)
    outgoing_features_handler.execute()


agid.register(outgoing_user_set_features)
