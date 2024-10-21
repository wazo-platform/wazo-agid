# Copyright 2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING

from wazo_agid import agid
from wazo_agid.handlers.outgoing_callerid_formatter import CallerIDFormatter

if TYPE_CHECKING:
    from psycopg2.extras import DictCursor

    from wazo_agid.agid import FastAGI


def format_and_set_outgoing_caller_id(
    agi: FastAGI, cursor: DictCursor, args: list[str]
) -> None:
    handler = CallerIDFormatter(agi, cursor, args)
    handler.execute()


agid.register(format_and_set_outgoing_caller_id)
