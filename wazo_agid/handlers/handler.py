# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

from wazo_agid import dialplan_variables

if TYPE_CHECKING:
    from wazo_agid.agid import FastAGI
    from psycopg2.extras import DictCursor


class Handler:
    def __init__(self, agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
        self._agi = agi
        self._cursor = cursor
        self._args = args

    def _set_path(self, path_type: str, path_id: str) -> None:
        # schedule path
        path = self._agi.get_variable(dialplan_variables.PATH)
        if path is None or len(path) == 0:
            self._agi.set_variable(dialplan_variables.PATH, path_type)
            self._agi.set_variable(dialplan_variables.PATH_ID, path_id)
