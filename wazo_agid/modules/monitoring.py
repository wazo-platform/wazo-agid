# Copyright 2009-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from psycopg2.extras import DictCursor

from wazo_agid import agid


def monitoring(agi: agid.FastAGI, cursor: DictCursor, args: list[str]) -> None:
    agi.send_command("Status: OK")


agid.register(monitoring)
