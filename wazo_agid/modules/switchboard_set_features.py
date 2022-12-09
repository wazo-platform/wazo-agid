# Copyright 2021-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_agid import agid
from wazo_agid.handlers.switchboardfeatures import SwitchboardFeatures


def switchboard_set_features(agi, cursor, args):
    switchboardfeatures_handler = SwitchboardFeatures(agi, cursor, args)
    switchboardfeatures_handler.execute()


agid.register(switchboard_set_features)
