# Copyright 2013-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from wazo_agid import dialplan_variables as dv

if TYPE_CHECKING:
    from psycopg2.extras import DictCursor

    from wazo_agid.agid import FastAGI

logger = logging.getLogger(__name__)


class Handler:
    def __init__(self, agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
        self._agi = agi
        self._cursor = cursor
        self._args = args

    def _set_path(self, path_type: str, path_id: str) -> None:
        # schedule path
        path = self._agi.get_variable(dv.PATH)
        if path is None or len(path) == 0:
            self._agi.set_variable(dv.PATH, path_type)
            self._agi.set_variable(dv.PATH_ID, path_id)

    def get_callee_channel(self) -> tuple[str, str] | None:
        visited: set[str] = set()
        channel = self._agi.env['agi_channel']
        while channel.startswith('Local/') and channel.endswith(';1'):
            if channel in visited:
                logger.debug('channel already visited, stopping infinite loop')
                break
            visited.add(channel)
            channel = channel.replace(';1', ';2')
            channel = self._agi.get_full_variable('${BRIDGEPEER}', channel)

        if not (
            callee_channel_id := self._agi.get_full_variable(
                '${CHANNEL(uniqueid)}', channel
            )
        ):
            logger.error('Could not get uniqueid for channel %s', channel)
            return None

        return channel, callee_channel_id
