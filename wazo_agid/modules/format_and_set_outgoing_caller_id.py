# Copyright 2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from psycopg2.extras import DictCursor

from wazo_agid import agid
from wazo_agid.agid import FastAGI
from wazo_agid.handlers.outgoing_callerid_formatter import CallerIDFormatter


def format_and_set_outgoing_caller_id(
    agi: FastAGI, cursor: DictCursor, args: list[str]
) -> None:
    handler = CallerIDFormatter(agi, cursor, args)
    handler.execute()


agid.register(format_and_set_outgoing_caller_id)
