# Copyright 2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from psycopg2.extras import DictCursor

from wazo_agid import agid

logger = logging.getLogger(__name__)


def pre_subroutine_compat(
    agi: agid.FastAGI, cursor: DictCursor, args: list[str]
) -> None:
    logger.debug('Entering pre-subroutine compatibility')


def post_subroutine_compat(
    agi: agid.FastAGI, cursor: DictCursor, args: list[str]
) -> None:
    logger.debug('Entering post-subroutine compatibility')


agid.register(pre_subroutine_compat)
agid.register(post_subroutine_compat)
