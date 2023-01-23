# Copyright 2021-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from psycopg2.extras import DictCursor

from wazo_agid import agid
from wazo_agid.handlers import queue


def queue_answered_call(agi: agid.FastAGI, cursor: DictCursor, args: list[str]) -> None:
    handler = queue.AnswerHandler(agi, cursor, args)
    handler.execute()


agid.register(queue_answered_call)
