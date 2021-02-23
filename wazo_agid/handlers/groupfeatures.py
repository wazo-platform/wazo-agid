# -*- coding: utf-8 -*-
# Copyright 2012-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import time
from uuid import uuid4

from wazo_agid.handlers.handler import Handler
from wazo_agid import objects
from wazo_agid import dialplan_variables
from wazo_agid.helpers import CallRecordingNameGenerator


class GroupFeatures(Handler):
    def __init__(self, agi, cursor, args):
        Handler.__init__(self, agi, cursor, args)
        self._call_recording_name_generator = CallRecordingNameGenerator(
            agi.config['call_recording']['filename_template'],
            agi.config['call_recording']['filename_extension'],
        )
        self._id = None
        self._referer = None
        self._exten = None
        self._context = None
        self._name = None
        self._timeout = None
        self._transfer_user = None
        self._transfer_call = None
        self._write_caller = None
        self._write_calling = None
        self._ignore_forward = None
        self._preprocess_subroutine = None
        self._musicclass = None
        self._pickup_member = None

    def execute(self):
        self._set_members()
        self._set_options()
        self._set_vars()
        self._set_preprocess_subroutine()
        self._set_timeout()
        self._set_dial_action()
        self._set_schedule()
        if self._needs_rewrite_cid():
            self._set_rewrite_cid()
        self._set_call_record_filename()

    def _needs_rewrite_cid(self):
        return self._referer == ("group:%s" % self._id)

    def _set_members(self):
        self._id = int(self._agi.get_variable(dialplan_variables.DESTINATION_ID))
        self._referer = self._agi.get_variable(dialplan_variables.FWD_REFERER)

        groupfeatures_columns = ('id', 'name',
                                 'timeout', 'transfer_user', 'transfer_call',
                                 'write_caller', 'write_calling', 'ignore_forward',
                                 'preprocess_subroutine', 'mark_answered_elsewhere')
        queue_columns = ('musicclass',)
        extensions_columns = ('exten', 'context')
        columns = (
            ["groupfeatures." + c for c in groupfeatures_columns] +
            ["queue." + c for c in queue_columns] +
            ["extensions." + c for c in extensions_columns]
        )

        self._cursor.query("SELECT ${columns} FROM groupfeatures "
                           "INNER JOIN queue "
                           "ON groupfeatures.name = queue.name "
                           "LEFT JOIN extensions "
                           "ON groupfeatures.id::text = extensions.typeval "
                           "AND extensions.type = 'group' "
                           "WHERE groupfeatures.id = %s "
                           "AND queue.category = 'group' "
                           "AND queue.commented = 0",
                           columns,
                           (self._id,))
        res = self._cursor.fetchone()

        if not res:
            raise LookupError("Unable to find group (id: %s)" % (self._id))

        self._exten = res['extensions.exten']
        self._context = res['extensions.context']
        self._name = res['groupfeatures.name']
        self._timeout = res['groupfeatures.timeout']
        self._transfer_user = res['groupfeatures.transfer_user']
        self._transfer_call = res['groupfeatures.transfer_call']
        self._write_caller = res['groupfeatures.write_caller']
        self._write_calling = res['groupfeatures.write_calling']
        self._ignore_forward = res['groupfeatures.ignore_forward']
        self._preprocess_subroutine = res['groupfeatures.preprocess_subroutine']
        self._musicclass = res['queue.musicclass']
        self._mark_answered_elsewhere = res['groupfeatures.mark_answered_elsewhere']

    def _set_vars(self):
        self._agi.set_variable('XIVO_REAL_NUMBER', self._exten)
        self._agi.set_variable('XIVO_REAL_CONTEXT', self._context)
        self._agi.set_variable('XIVO_GROUPNAME', self._name)
        if self._musicclass:
            self._agi.set_variable('CHANNEL(musicclass)', self._musicclass)

    def _set_options(self):
        options = ""
        needanswer = "1"

        if self._transfer_user:
            options += "t"

        if self._transfer_call:
            options += "T"

        if self._write_caller:
            options += "x"

        if self._write_calling:
            options += "X"

        if self._ignore_forward:
            options += 'i'

        if not self._musicclass:
            options += "r"
            needanswer = "0"

        if self._mark_answered_elsewhere:
            options += "C"

        self._agi.set_variable('XIVO_GROUPOPTIONS', options)
        self._agi.set_variable('XIVO_GROUPNEEDANSWER', needanswer)

    def _set_preprocess_subroutine(self):
        if self._preprocess_subroutine:
            self._agi.set_variable('XIVO_GROUPPREPROCESS_SUBROUTINE', self._preprocess_subroutine)

    def _set_timeout(self):
        if self._timeout:
            self._agi.set_variable('XIVO_GROUPTIMEOUT', self._timeout)
        else:
            self._agi.set_variable('XIVO_GROUPTIMEOUT', "")

    def _set_dial_action(self):
        for event in ('noanswer', 'congestion', 'busy', 'chanunavail'):
            objects.DialAction(self._agi, self._cursor, event, "group", self._id).set_variables()

    def _set_rewrite_cid(self):
        objects.CallerID(self._agi, self._cursor, 'group', self._id).rewrite(force_rewrite=False)

    def _set_schedule(self):
        path = self._agi.get_variable('XIVO_PATH')
        if path is None or len(path) == 0:
            self._agi.set_variable('XIVO_PATH', 'group')
            self._agi.set_variable('XIVO_PATH_ID', self._id)

    def _set_call_record_filename(self):
        args = {
            'srcnum': self._agi.get_variable(dialplan_variables.SOURCE_NUMBER),
            'dstnum': self._exten,
            'timestamp': int(time.time()),
            'local_time': time.asctime(time.localtime()),
            'utc_time': time.asctime(time.gmtime()),
            'base_context': self._context,
            'tenant_uuid': self._agi.get_variable(dialplan_variables.TENANT_UUID),
            'dest_type': 'group',
        }

        self._agi.set_variable(
            '__WAZO_CALL_RECORD_FILE_CALLEE',
            self._call_recording_name_generator.generate(side='callee', **args),
        )
        self._agi.set_variable(
            '__WAZO_CALL_RECORD_FILE_CALLER',
            self._call_recording_name_generator.generate(side='caller', **args),
        )
        self._agi.set_variable('WAZO_CALL_RECORD_SIDE', 'caller')
        self._agi.set_variable('__WAZO_LOCAL_CHAN_MATCH_UUID', str(uuid4()))
