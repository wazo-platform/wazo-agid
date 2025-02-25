# Copyright 2006-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from psycopg2.extras import DictCursor

from wazo_agid import agid
from wazo_agid.handlers.userfeatures import UserFeatures


def incoming_user_set_features(
    agi: agid.FastAGI, cursor: DictCursor, args: list[str]
) -> None:
    userfeatures_handler = UserFeatures(agi, cursor, args)
    userfeatures_handler.execute()


agid.register(incoming_user_set_features)
