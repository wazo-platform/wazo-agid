# Copyright 2006-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from wazo_agid import agid

if TYPE_CHECKING:
    from psycopg2.extras import DictCursor

    from wazo_agid.agid import FastAGI


logger = logging.getLogger(__name__)


def fwdundoall(agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
    user_id = _get_id_of_calling_user(agi)
    _user_disable_all_forwards(agi, user_id)


def _get_id_of_calling_user(agi: FastAGI) -> int:
    return int(agi.get_variable('WAZO_USERID'))


def _user_disable_all_forwards(agi: FastAGI, user_id: int) -> None:
    try:
        confd_client = agi.config['confd']['client']
        disabled = {'enabled': False}
        body = {'busy': disabled, 'noanswer': disabled, 'unconditional': disabled}
        confd_client.users(user_id).update_forwards(body)
    except Exception as e:
        logger.error('Error during disabling all forwards: %s', e)


agid.register(fwdundoall)
