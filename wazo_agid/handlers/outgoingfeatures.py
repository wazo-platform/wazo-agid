# -*- coding: utf-8 -*-
# Copyright 2006-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import time
import logging

from xivo_dao import context_dao

from wazo_agid import dialplan_variables
from wazo_agid.handlers.handler import Handler
from wazo_agid.helpers import CallRecordingNameGenerator
from wazo_agid import objects

logger = logging.getLogger(__name__)


class OutgoingFeatures(Handler):

    PATH_TYPE = 'outcall'

    def __init__(self, agi, cursor, args):
        Handler.__init__(self, agi, cursor, args)
        self._call_recording_name_generator = CallRecordingNameGenerator(
            agi.config['call_recording']['filename_template'],
            agi.config['call_recording']['filename_extension'],
        )
        self.user = None
        self.userid = None
        self.callerid = None
        self.callrecord = False
        self.options = ""
        self._context = None
        self.outcall = objects.Outcall(self._agi, self._cursor)

    def _retrieve_outcall(self):
        try:
            self.outcall.retrieve_values(self.dialpattern_id)
        except (ValueError, LookupError) as e:
            self._agi.dp_break(str(e))

    def _set_destination_number(self):
        if self.outcall.stripnum > 0:
            self.dstnum = self.dstnum[self.outcall.stripnum:]
        if self.outcall.externprefix:
            self.dstnum = self.outcall.externprefix + self.dstnum

    def _retrieve_user(self):
        try:
            self.user = objects.User(self._agi, self._cursor, int(self.userid))
            if self.user.enablexfer:
                self.options += 'T'

            if not self.outcall.internal:
                if self.user.enableonlinerec:
                    self.options += "X"
                self.callrecord = self.user.callrecord
        except (ValueError, LookupError):
            logger.debug('Could not retrieve user %s', self.userid)
        self._agi.set_variable(dialplan_variables.CALL_OPTIONS, self.options)

    def _set_userfield(self):
        if self.user and self.user.userfield:
            self._agi.set_variable('CHANNEL(userfield)', self.user.userfield)

    def _set_caller_id(self):
        if self.outcall.internal:
            return

        if self.user is None or self.user.outcallerid == 'default':
            if self.outcall.callerid:
                objects.CallerID.set(self._agi, self.outcall.callerid)
        elif self.user.outcallerid == 'anonymous':
            self._agi.set_variable('CALLERID(name-pres)', 'prohib')
            self._agi.set_variable('CALLERID(num-pres)', 'prohib')
        else:
            objects.CallerID.set(self._agi, self.user.outcallerid)

    def _set_trunk_info(self):
        for i, trunk in enumerate(self.outcall.trunks):
            # TODO PJSIP clean after migration
            if trunk.interface.startswith('SIP'):
                suffix = trunk.interface.replace('SIP/', '')
                exten = '{exten}@{name}'.format(exten=self.dstnum, name=suffix)
                self._agi.set_variable('%s%d' % (dialplan_variables.INTERFACE, i), 'PJSIP')
                self._agi.set_variable('%s%d' % (dialplan_variables.TRUNK_EXTEN, i), exten)
            else:
                self._agi.set_variable('%s%d' % (dialplan_variables.INTERFACE, i), trunk.interface)
                self._agi.set_variable('%s%d' % (dialplan_variables.TRUNK_EXTEN, i), self.dstnum)
            if trunk.intfsuffix:
                intfsuffix = trunk.intfsuffix
            else:
                intfsuffix = ""
            self._agi.set_variable('%s%d' % (dialplan_variables.TRUNK_SUFFIX, i), intfsuffix)

    def _set_record_file_name(self):
        callrecordfile = self._build_call_record_file_name() or ''
        self._agi.set_variable(dialplan_variables.CALL_RECORD_FILE_NAME, callrecordfile)

    def _build_call_record_file_name(self):
        if not self.callrecord:
            return

        args = {
            'srcnum': self.srcnum,
            'dstnum': self.orig_dstnum,
            'timestamp': int(time.time()),
            'local_time': time.asctime(time.localtime()),
            'utc_time': time.asctime(time.gmtime()),
            'base_context': self._context,
        }
        return self._call_recording_name_generator.generate(args)

    def _set_preprocess_subroutine(self):
        if self.outcall.preprocess_subroutine:
            preprocess_subroutine = self.outcall.preprocess_subroutine
        else:
            preprocess_subroutine = ""
        self._agi.set_variable(dialplan_variables.OUTCALL_PREPROCESS_SUBROUTINE, preprocess_subroutine)

    def _set_hangup_ring_time(self):
        if self.outcall.hangupringtime:
            hangupringtime = self.outcall.hangupringtime
        else:
            hangupringtime = ""
        self._agi.set_variable(dialplan_variables.HANGUP_RING_TIME, hangupringtime)

    def _extract_dialplan_variables(self):
        self.userid = self._agi.get_variable(dialplan_variables.USERID)
        self.dialpattern_id = self._agi.get_variable(dialplan_variables.DESTINATION_ID)
        self.dstnum = self._agi.get_variable(dialplan_variables.DESTINATION_NUMBER)
        self.srcnum = self._agi.get_variable(dialplan_variables.SOURCE_NUMBER)
        self.orig_dstnum = self.dstnum
        self._context = self._agi.get_variable(dialplan_variables.BASE_CONTEXT)

    def execute(self):
        self._extract_dialplan_variables()
        self._retrieve_outcall()
        self._set_destination_number()
        self._retrieve_user()
        self._set_userfield()
        self._set_caller_id()
        self._set_trunk_info()
        self._set_record_file_name()
        self._set_preprocess_subroutine()
        self._set_hangup_ring_time()
        self._agi.set_variable(dialplan_variables.OUTCALL_ID, self.outcall.id)
        self._set_path(OutgoingFeatures.PATH_TYPE, self.outcall.id)
