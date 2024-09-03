# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
from collections.abc import Generator
from typing import TYPE_CHECKING

from wazo_agid import agid
from wazo_agid.helpers import build_sip_interface

if TYPE_CHECKING:
    from psycopg2.extras import DictCursor

    from wazo_agid.agid import FastAGI


logger = logging.getLogger(__name__)


class UnknownUser(Exception):
    pass


class _UserLine:
    def __init__(self, agi: FastAGI, user_uuid: str) -> None:
        self._agi = agi
        self._user_uuid = user_uuid
        self.interfaces = []
        hint = agi.get_variable(f'HINT({user_uuid}@usersharedlines)')
        if not hint:
            logger.error('No hint found for %s', f'{user_uuid}@usersharedlines')
            raise UnknownUser(user_uuid)

        for endpoint in hint.split('&'):
            if '/' not in endpoint:
                continue

            for interface in self._find_matching_interfaces(endpoint):
                self.interfaces.append(interface)

    def _find_matching_interfaces(self, endpoint: str) -> Generator[str, None, None]:
        protocol, name = endpoint.split('/', 1)
        if protocol == 'PJSIP':
            contacts = build_sip_interface(self._agi, self._user_uuid, name)
            yield from contacts.split('&')
        else:
            yield endpoint


def get_user_interfaces(agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
    user_uuid = args[0]
    user_line = _UserLine(agi, user_uuid)
    agi.set_variable('WAZO_USER_INTERFACES', '&'.join(user_line.interfaces))


agid.register(get_user_interfaces)
