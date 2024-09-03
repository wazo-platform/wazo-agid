# Copyright 2006-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from psycopg2.extras import DictCursor

from wazo_agid import agid
from wazo_agid.handlers.groupfeatures import GroupFeatures


def incoming_group_set_features(
    agi: agid.FastAGI, cursor: DictCursor, args: list[str]
) -> None:
    groupfeatures_handler = GroupFeatures(agi, cursor, args)
    groupfeatures_handler.execute()


agid.register(incoming_group_set_features)
