# -*- coding: UTF-8 -*-

__license__ = """
    Copyright (C) 2012  Avencall

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from xivo_agid.handlers.handler import Handler
from xivo_agid import objects
from xivo_agid import dialplan_variables

import time


class UserFeatures(Handler):

    PATH_TYPE = 'user'

    def __init__(self, agi, cursor, args):
        Handler.__init__(self, agi, cursor, args)
        self._userid = None
        self._dstid = None
        self._lineid = None
        self._zone = None
        self._bypass_filter = None
        self._srcnum = None
        self._dstnum = None
        self._feature_list = None
        self._caller = None
        self._lines = None
        self._master_line = None
        self._user = None

    def execute(self):
        self._set_members()
        self._set_xivo_ifaces()
        self._set_user_filter()
        abort = self._boss_secretary_filter()
        if abort:
            return
        self._set_options()
        self._set_simultcalls()
        self._set_ringseconds()
        self._set_enablednd()
        self._set_mailbox()
        self._set_call_forwards()
        self._set_dial_action_congestion()
        self._set_dial_action_chanunavail()
        self._set_music_on_hold()
        self._set_call_recordfile()
        self._set_preprocess_subroutine()
        self._set_mobile_number()
        self._set_vmbox_lang()
        self._set_path(UserFeatures.PATH_TYPE, self._user.id)

    def _set_members(self):
        self._userid = self._agi.get_variable(dialplan_variables.USERID)
        self._dstid = self._agi.get_variable(dialplan_variables.DESTINATION_ID)
        self._lineid = self._agi.get_variable(dialplan_variables.LINE_ID)
        self._zone = self._agi.get_variable(dialplan_variables.CALL_ORIGIN)
        self._bypass_filter = self._agi.get_variable(dialplan_variables.CALLFILTER_BYPASS)
        self._srcnum = self._agi.get_variable(dialplan_variables.SOURCE_NUMBER)
        self._dstnum = self._agi.get_variable(dialplan_variables.DESTINATION_NUMBER)
        self._set_feature_list()
        self._set_caller()
        self._set_lines()
        self._set_user()

    def _set_feature_list(self):
        self._feature_list = objects.ExtenFeatures(self._agi, self._cursor)

    def _set_caller(self):
        if self._userid:
            try:
                self._caller = objects.User(self._agi, self._cursor, int(self._userid))
            except (ValueError, LookupError):
                self._caller = None

    def _set_lines(self):
        if self._dstid:
            try:
                self._lines = objects.Lines(self._agi, self._cursor, int(self._dstid))
            except (ValueError, LookupError), e:
                self._agi.dp_break(str(e))
            else:
                self._master_line = self._lines.lines[0]
                self._agi.set_variable('XIVO_DST_USERNUM', self._master_line['number'])

    def _set_user(self):
        if self._dstid:
            try:
                self._user = objects.User(self._agi, self._cursor, int(self._dstid))
            except (ValueError, LookupError), e:
                self._agi.dp_break(str(e))
            self._set_xivo_user_name()

    def _is_main_line(self):
        return self._lineid and str(self._master_line['id']) == self._lineid

    def _ring_main_line_only(self):
        try:
            curline = [line for line in self._lines.lines if str(line['id']) == self._lineid][0]
            self._set_xivo_iface_nb(1)
            if curline['protocol'].lower() == 'custom':
                self._agi.set_variable('XIVO_INTERFACE_0', "%s" % (curline['name']))
            else:
                self._agi.set_variable('XIVO_INTERFACE_0', "%s/%s" % (curline['protocol'], curline['name']))
        except Exception:
            pass

    def _ring_line_sequence(self):
        num = 0
        curlines = []
        for line in self._lines.lines:
            if num < line['num']:
                self._agi.set_variable('XIVO_INTERFACE_%d' % num, '&'.join(curlines))
                num += 1
                del curlines[:]
            curlines.append('%s/%s' % (line['protocol'], line['name']))
        if len(curlines) > 0:
            self._agi.set_variable('XIVO_INTERFACE_%d' % num, '&'.join(curlines))
            num += 1
        self._agi.set_variable('XIVO_INTERFACE_NB', num)

    def _set_xivo_ifaces(self):
        self._set_xivo_iface_nb(0)
        if self._is_main_line():
            self._ring_main_line_only()
        else:
            self._ring_line_sequence()

    def _set_xivo_user_name(self):
        if self._user:
            if self._user.firstname:
                self._agi.set_variable('XIVO_DST_FIRSTNAME', self._user.firstname)
            if self._user.lastname:
                self._agi.set_variable('XIVO_DST_LASTNAME', self._user.lastname)

    def _set_user_filter(self):
        self._user_filter = self._user.filter

    def _set_xivo_iface_nb(self, number):
        self._agi.set_variable('XIVO_INTERFACE_NB', 0)

    def _boss_secretary_filter(self):
        # Special case. If a boss-secretary filter is set, the code will prematurely
        # exit because the other normally set variables are skipped.
        if not self._bypass_filter and self._user_filter and self._user_filter.active:
            zone_applies = self._user_filter.check_zone(self._zone)
            if self._caller:
                secretary = self._user_filter.get_secretary_by_id(self._caller.id)
            else:
                secretary = None
            if zone_applies and not secretary:
                if self._user_filter.mode in ("bossfirst-simult", "bossfirst-serial", "all"):
                    self._agi.set_variable('XIVO_CALLFILTER_BOSS_INTERFACE', self._user_filter.boss.interface)
                    self._agi.set_variable('XIVO_CALLFILTER_BOSS_TIMEOUT', self._user_filter.boss.ringseconds)
                if self._user_filter.mode in ("bossfirst-simult", "secretary-simult", "all"):
                    interface = '&'.join(secretary.interface for secretary in self._user_filter.secretaries if secretary.active)
                    self._agi.set_variable('XIVO_CALLFILTER_INTERFACE', interface)
                    self._agi.set_variable('XIVO_CALLFILTER_TIMEOUT', self._user_filter.ringseconds)
                elif self._user_filter.mode in ("bossfirst-serial", "secretary-serial"):
                    index = 0
                    for secretary in self._user_filter.secretaries:
                        if secretary.active:
                            self._agi.set_variable('XIVO_CALLFILTER_SECRETARY%d_INTERFACE' % (index,), secretary.interface)
                            self._agi.set_variable('XIVO_CALLFILTER_SECRETARY%d_TIMEOUT' % (index,), secretary.ringseconds)
                            index += 1

                self._user_filter.set_dial_actions()
                self._user_filter.rewrite_cid()
                self._agi.set_variable('XIVO_CALLFILTER', '1')
                self._agi.set_variable('XIVO_CALLFILTER_MODE', self._user_filter.mode)
                return True
        return False

    def _set_mailbox(self):
        self._mailbox = ""
        self._mailbox_context = ""
        useremail = ""
        if self._user.vmbox:
            self._mailbox = self._user.vmbox.mailbox
            self._mailbox_context = self._user.vmbox.context
            if self._user.vmbox.email:
                useremail = self._user.vmbox.email
        self._agi.set_variable('XIVO_ENABLEVOICEMAIL', self._user.enablevoicemail)
        self._agi.set_variable('XIVO_MAILBOX', self._mailbox)
        self._agi.set_variable('XIVO_MAILBOX_CONTEXT', self._mailbox_context)
        self._agi.set_variable('XIVO_USEREMAIL', useremail)

    def _set_vmbox_lang(self):
        vmbox = None
        if len(self._mailbox) > 0:
            try:
                vmbox = objects.VMBox(self._agi, self._cursor, mailbox=self._mailbox, context=self._mailbox_context)
            except (ValueError, LookupError) as e:
                self._agi.dp_break(str(e))
        mbox_lang = ''
        if self._zone == 'intern' and self._caller and self._caller.language:
            mbox_lang = self._caller.language
        elif vmbox and vmbox.language:
            mbox_lang = vmbox.language
        elif self._user and self._user.language:
            mbox_lang = self._user.language
        self._agi.set_variable('XIVO_MAILBOX_LANGUAGE', mbox_lang)

    def _set_mobile_number(self):
        if self._user.mobilephonenumber:
            mobilephonenumber = self._user.mobilephonenumber
        else:
            mobilephonenumber = ""
        self._agi.set_variable('XIVO_MOBILEPHONENUMBER', mobilephonenumber)

    def _set_preprocess_subroutine(self):
        if self._user.preprocess_subroutine:
            preprocess_subroutine = self._user.preprocess_subroutine
        else:
            preprocess_subroutine = ""
        self._agi.set_variable('XIVO_USERPREPROCESS_SUBROUTINE', preprocess_subroutine)

    def _set_call_recordfile(self):
        callrecordfile = ""
        if self._feature_list.callrecord:
            if self._user.callrecord or (self._caller and self._caller.callrecord):
                callrecordfile = "user-%s-%s-%s.wav" % (self._srcnum, self._dstnum, int(time.time()))
            else:
                callrecordfile = ""
        else:
            callrecordfile = ""
        self._agi.set_variable('XIVO_CALLRECORDFILE', callrecordfile)

    def _set_music_on_hold(self):
        if self._user.musiconhold:
            self._agi.set_variable('CHANNEL(musicclass)', self._user.musiconhold)

    def _set_options(self):
        options = "hH"
        if self._user.enablexfer:
            options += "t"
        if self._caller and self._caller.enablexfer:
            options += "T"
        if self._user.enableautomon:
            options += "w"
        if self._caller and self._caller.enableautomon:
            options += "W"
        if self._feature_list.incallfilter and self._user.incallfilter:
            options += "p"
        self._agi.set_variable('XIVO_CALLOPTIONS', options)

    def _set_ringseconds(self):
        if self._user.ringseconds > 0:
            ringseconds = self._user.ringseconds
        else:
            ringseconds = ""
        self._agi.set_variable('XIVO_RINGSECONDS', ringseconds)

    def _set_simultcalls(self):
        return self._agi.set_variable('XIVO_SIMULTCALLS', self._user.simultcalls)

    def _set_enablednd(self):
        if self._feature_list.enablednd:
            enablednd = self._user.enablednd
        else:
            enablednd = 0
        self._agi.set_variable('XIVO_ENABLEDND', enablednd)

    def _setrna(self, called_line):
        setrna = False
        enablerna = 0
        rna_action = 'none'
        rna_actionarg1 = ""
        rna_actionarg2 = ""
        if self._feature_list.fwdrna:
            enablerna = self._user.enablerna
            if enablerna and 'context' in called_line:
                rna_action = 'extension'
                rna_actionarg1 = self._user.destrna
                rna_actionarg2 = called_line['context']
            else:
                setrna = True
                objects.DialAction(self._agi, self._cursor, 'noanswer', 'user', self._user.id).set_variables()
        self._agi.set_variable('XIVO_ENABLERNA', enablerna)
        if not setrna:
            objects.DialAction.set_agi_variables(self._agi, 'noanswer', 'user', rna_action, rna_actionarg1, rna_actionarg2, False)

    def _setbusy(self, called_line):
        setbusy = False
        enablebusy = 0
        busy_action = 'none'
        busy_actionarg1 = ""
        busy_actionarg2 = ""
        if self._feature_list.fwdbusy:
            enablebusy = self._user.enablebusy
            if enablebusy and 'context' in called_line:
                busy_action = 'extension'
                busy_actionarg1 = self._user.destbusy
                busy_actionarg2 = called_line['context']
            else:
                setbusy = True
                objects.DialAction(self._agi, self._cursor, 'busy', 'user', self._user.id).set_variables()
        self._agi.set_variable('XIVO_ENABLEBUSY', enablebusy)
        if not setbusy:
            objects.DialAction.set_agi_variables(self._agi, 'busy', 'user', busy_action, busy_actionarg1, busy_actionarg2, False)

    def _set_enableunc(self, called_line):
        enableunc = 0
        unc_action = 'none'
        unc_actionarg1 = ""
        unc_actionarg2 = ""
        if self._feature_list.fwdunc:
            enableunc = self._user.enableunc
            if enableunc and 'context' in called_line:
                unc_action = 'extension'
                unc_actionarg1 = self._user.destunc
                unc_actionarg2 = called_line['context']
        self._agi.set_variable('XIVO_ENABLEUNC', enableunc)
        objects.DialAction.set_agi_variables(self._agi, 'unc', 'user', unc_action, unc_actionarg1, unc_actionarg2, False)

    def _set_call_forwards(self):
        called_line = self._master_line
        self._set_enableunc(called_line)
        self._setbusy(called_line)
        self._setrna(called_line)

    def _set_dial_action_congestion(self):
        objects.DialAction(self._agi, self._cursor, 'congestion', 'user', self._user.id).set_variables()

    def _set_dial_action_chanunavail(self):
        objects.DialAction(self._agi, self._cursor, 'chanunavail', 'user', self._user.id).set_variables()
