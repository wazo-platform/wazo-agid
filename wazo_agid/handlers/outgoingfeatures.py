# Copyright 2006-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from wazo_agid import dialplan_variables, objects
from wazo_agid.handlers.handler import Handler

if TYPE_CHECKING:
    from psycopg2.extras import DictCursor

    from wazo_agid.agid import FastAGI

logger = logging.getLogger(__name__)


class OutgoingFeatures(Handler):
    PATH_TYPE = 'outcall'

    dstnum: str
    dialpattern_id: str

    def __init__(self, agi: FastAGI, cursor: DictCursor, args: list[str]) -> None:
        super().__init__(agi, cursor, args)
        self.user: objects.User | None = None
        self.userid: int | str | None = None
        self.callerid = None
        self.callrecord = False
        self.options = ""
        self._context: str | None = None
        self.outcall = objects.Outcall(self._agi, self._cursor)
        self._tenant_uuid: str | None = None

    def _retrieve_outcall(self) -> None:
        try:
            self.outcall.retrieve_values(self.dialpattern_id)
        except (ValueError, LookupError) as e:
            self._agi.dp_break(str(e))

    def _set_call_record_side(self) -> None:
        self._agi.set_variable('WAZO_CALL_RECORD_SIDE', 'caller')

    def _set_destination_number(self) -> None:
        if self.outcall.stripnum and self.outcall.stripnum > 0:
            self.dstnum = self.dstnum[self.outcall.stripnum :]
        if self.outcall.externprefix:
            self.dstnum = self.outcall.externprefix + self.dstnum

    def _retrieve_user(self) -> None:
        try:
            userid: int | str
            if not self.userid:
                userid = self.useruuid
            else:
                userid = int(self.userid)
            self.user = objects.User(self._agi, self._cursor, userid)
            if self.user.enablexfer:
                self.options += 'T'

            if not self.outcall.internal:
                if self.user.enableonlinerec:
                    self.options += "X"
                self.callrecord = self.user.call_record_outgoing_external_enabled
        except (ValueError, LookupError):
            logger.debug('Could not retrieve user %s', self.userid)
        self._agi.set_variable(dialplan_variables.CALL_OPTIONS, self.options)

    def _set_userfield(self) -> None:
        if self.user and self.user.userfield:
            self._agi.set_variable('CHANNEL(userfield)', self.user.userfield)

    def _set_user_music_on_hold(self) -> None:
        if self.user and self.user.musiconhold:
            self._agi.set_variable('CHANNEL(musicclass)', self.user.musiconhold)

    def _set_caller_id(self) -> None:
        if self.outcall.internal:
            logger.debug(
                '%s: _set_caller_id: skipping caller id update: outcall set to internal caller ID',
                self._agi.env['agi_channel'],
            )
            return

        if self.user is None or self.user.outcallerid == 'default':
            if self.outcall.callerid:
                logger.debug(
                    '%s: _set_caller_id: using outcall caller ID',
                    self._agi.env['agi_channel'],
                )
                objects.CallerID.set(self._agi, self.outcall.callerid)
            else:
                logger.debug(
                    '%s: _set_caller_id: using user default caller ID',
                    self._agi.env['agi_channel'],
                )
        elif self.user.outcallerid == 'anonymous':
            logger.debug(
                '%s: _set_caller_id: using anonymous caller ID',
                self._agi.env['agi_channel'],
            )
            self._agi.set_variable('CALLERID(name-pres)', 'prohib')
            self._agi.set_variable('CALLERID(num-pres)', 'prohib')
        else:
            logger.debug(
                '%s: _set_caller_id: using user outgoing caller ID',
                self._agi.env['agi_channel'],
            )
            objects.CallerID.set(self._agi, self.user.outcallerid)

    def _set_trunk_info(self) -> None:
        for i, trunk in enumerate(self.outcall.trunks):
            if trunk.interface.startswith('PJSIP'):
                name = trunk.interface.replace('PJSIP/', '')
                exten = f'{self.dstnum}@{name}'
                self._agi.set_variable(f'{dialplan_variables.INTERFACE}{i:d}', 'PJSIP')
                self._agi.set_variable(f'{dialplan_variables.TRUNK_EXTEN}{i:d}', exten)
            else:
                self._agi.set_variable(
                    f'{dialplan_variables.INTERFACE}{i:d}', trunk.interface
                )
                self._agi.set_variable(
                    f'{dialplan_variables.TRUNK_EXTEN}{i:d}', self.dstnum
                )
            if trunk.intfsuffix:
                intfsuffix = trunk.intfsuffix
            else:
                intfsuffix = ""
            self._agi.set_variable(
                f'{dialplan_variables.TRUNK_SUFFIX}{i:d}', intfsuffix
            )

    def _set_preprocess_subroutine(self) -> None:
        if self.outcall.preprocess_subroutine:
            preprocess_subroutine = self.outcall.preprocess_subroutine
        else:
            preprocess_subroutine = ""
        self._agi.set_variable(
            dialplan_variables.OUTCALL_PREPROCESS_SUBROUTINE, preprocess_subroutine
        )

    def _set_hangup_ring_time(self) -> None:
        if self.outcall.hangupringtime:
            hangupringtime = self.outcall.hangupringtime
        else:
            hangupringtime = ""
        self._agi.set_variable(dialplan_variables.HANGUP_RING_TIME, hangupringtime)

    def _extract_dialplan_variables(self) -> None:
        self.userid = self._agi.get_variable(dialplan_variables.USERID)
        self.useruuid = self._agi.get_variable(dialplan_variables.USERUUID)
        self.dialpattern_id = self._agi.get_variable(dialplan_variables.DESTINATION_ID)
        self.dstnum = self._agi.get_variable(dialplan_variables.DESTINATION_NUMBER)
        self.srcnum = self._agi.get_variable(dialplan_variables.SOURCE_NUMBER)
        self.orig_dstnum = self.dstnum
        self._context = self._agi.get_variable(dialplan_variables.BASE_CONTEXT)
        self._tenant_uuid = self._agi.get_variable(dialplan_variables.TENANT_UUID)

    def execute(self) -> None:
        self._extract_dialplan_variables()
        self._retrieve_outcall()
        self._set_destination_number()
        self._retrieve_user()
        self._set_userfield()
        self._set_user_music_on_hold()
        self._set_caller_id()
        self._set_trunk_info()
        self._set_preprocess_subroutine()
        self._set_hangup_ring_time()
        self._agi.set_variable(dialplan_variables.OUTCALL_ID, self.outcall.id)
        self._set_path(OutgoingFeatures.PATH_TYPE, self.outcall.id)
        self._set_call_record_side()
