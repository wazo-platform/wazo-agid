# Copyright 2021-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from psycopg2.extras import DictCursor

from wazo_agid import agid
from wazo_agid.handlers.switchboardfeatures import SwitchboardFeatures


def switchboard_set_features(
    agi: agid.FastAGI, cursor: DictCursor, args: list[str]
) -> None:
    switchboardfeatures_handler = SwitchboardFeatures(agi, cursor, args)
    switchboardfeatures_handler.execute()


agid.register(switchboard_set_features)
