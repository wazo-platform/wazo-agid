# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from wazo_agid import agid

if TYPE_CHECKING:
    from psycopg2.extras import DictCursor

    from wazo_agid.agid import FastAGI


logger = logging.getLogger(__name__)


def linear_group_check_timeout(
    agi: FastAGI, cursor: DictCursor, args: list[str]
) -> None:
    group_id = agi.get_variable('WAZO_DSTID')

    if not (_group_timeout := agi.get_variable('XIVO_GROUPTIMEOUT')):
        logger.info('XIVO_GROUPTIMEOUT not set for group %s', group_id)
        return
    else:
        group_timeout = float(_group_timeout)

    current_time = time.time()

    if not (_start_time := agi.get_variable('WAZO_GROUP_START_TIME')):
        start_time = current_time
        agi.set_variable('WAZO_GROUP_START_TIME', str(start_time))
        return
    else:
        start_time = float(_start_time)

    if (current_time - start_time) >= group_timeout:
        agi.set_variable('WAZO_GROUP_TIMEOUT_EXPIRED', '1')


agid.register(linear_group_check_timeout)
