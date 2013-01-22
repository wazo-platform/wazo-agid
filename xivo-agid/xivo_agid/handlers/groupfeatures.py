# -*- coding: utf-8 -*-

# Copyright (C) 2012-2013 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from xivo_agid.handlers.handler import Handler
from xivo_agid import objects
from xivo_agid import dialplan_variables


class GroupFeatures(Handler):
    def __init__(self, agi, cursor, args):
        Handler.__init__(self, agi, cursor, args)
        self._id = None
        self._referer = None
        self._number = None
        self._context = None
        self._name = None
        self._timeout = None
        self._transfer_user = None
        self._transfer_call = None
        self._write_caller = None
        self._write_calling = None
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

    def _needs_rewrite_cid(self):
        return (self._referer == ("group:%s" % self._id) or self._referer.startswith("voicemenu:"))

    def _set_members(self):
        self._id = int(self._agi.get_variable(dialplan_variables.DESTINATION_ID))
        self._referer = self._agi.get_variable(dialplan_variables.FWD_REFERER)

        groupfeatures_columns = ('id', 'number', 'context', 'name',
                                 'timeout', 'transfer_user', 'transfer_call',
                                 'write_caller', 'write_calling', 'preprocess_subroutine')
        queue_columns = ('musicclass',)
        columns = ["groupfeatures." + c for c in groupfeatures_columns] + ["queue." + c for c in queue_columns]

        self._cursor.query("SELECT ${columns} FROM groupfeatures "
                           "INNER JOIN queue "
                           "ON groupfeatures.name = queue.name "
                           "WHERE groupfeatures.id = %s "
                           "AND groupfeatures.deleted = 0 "
                           "AND queue.category = 'group' "
                           "AND queue.commented = 0",
                           columns,
                           (self._id,))
        res = self._cursor.fetchone()

        if not res:
            raise LookupError("Unable to find group (id: %s)" % (self._id))

        self._number = res['groupfeatures.number']
        self._context = res['groupfeatures.context']
        self._name = res['groupfeatures.name']
        self._timeout = res['groupfeatures.timeout']
        self._transfer_user = res['groupfeatures.transfer_user']
        self._transfer_call = res['groupfeatures.transfer_call']
        self._write_caller = res['groupfeatures.write_caller']
        self._write_calling = res['groupfeatures.write_calling']
        self._preprocess_subroutine = res['groupfeatures.preprocess_subroutine']
        self._musicclass = res['queue.musicclass']

    def _set_vars(self):
        self._agi.set_variable('XIVO_REAL_NUMBER', self._number)
        self._agi.set_variable('XIVO_REAL_CONTEXT', self._context)
        self._agi.set_variable('XIVO_GROUPNAME', self._name)

    def _set_options(self):
        options = ""
        needanswer = "1"

        if self._transfer_user:
            options += "t"

        if self._transfer_call:
            options += "T"

        if self._write_caller:
            options += "w"

        if self._write_calling:
            options += "W"

        if not self._musicclass:
            options += "r"
            needanswer = "0"

        self._agi.set_variable('XIVO_GROUPOPTIONS', options)
        self._agi.set_variable('XIVO_GROUPNEEDANSWER', needanswer)

    def _set_preprocess_subroutine(self):
        if self._preprocess_subroutine:
            self._agi.set_variable('XIVO_GROUPPREPROCESS_SUBROUTINE', self._preprocess_subroutine)

    def _set_timeout(self):
        if self._timeout:
            self._agi.set_variable('XIVO_GROUPTIMEOUT', self._timeout)

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
