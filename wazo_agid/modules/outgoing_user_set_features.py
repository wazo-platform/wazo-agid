# Copyright 2006-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from psycopg2.extras import DictCursor

from wazo_agid import agid
from wazo_agid.handlers.outgoingfeatures import OutgoingFeatures


def outgoing_user_set_features(
    agi: agid.FastAGI, cursor: DictCursor, args: list[str]
) -> None:
    outgoing_features_handler = OutgoingFeatures(agi, cursor, args)
    outgoing_features_handler.execute()


agid.register(outgoing_user_set_features)
