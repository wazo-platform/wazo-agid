# -*- coding: utf-8 -*-

# Copyright (C) 2012-2014 Avencall
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

from xivo_dao import callfilter_dao, user_line_dao
from xivo_agid.objects import DialAction, CallerID
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
        self._zone = None
        self._srcnum = None
        self._dstnum = None
        self._feature_list = None
        self._caller = None
        self._line = None
        self._user = None

    def execute(self):
        self._set_members()
        self._set_xivo_iface()

        filtered = self._call_filtering()
        if filtered:
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
        self._zone = self._agi.get_variable(dialplan_variables.CALL_ORIGIN)
        self._srcnum = self._agi.get_variable(dialplan_variables.SOURCE_NUMBER)
        self._dstnum = self._agi.get_variable(dialplan_variables.DESTINATION_NUMBER)
        self._set_feature_list()
        self._set_caller()
        self._set_line()
        self._set_user()

    def _set_feature_list(self):
        self._feature_list = objects.ExtenFeatures(self._agi, self._cursor)

    def _set_caller(self):
        if self._userid:
            try:
                self._caller = objects.User(self._agi, self._cursor, int(self._userid))
            except (ValueError, LookupError):
                self._caller = None

    def _set_line(self):
        if self._dstid:
            try:
                self._line = objects.Line(int(self._dstid))
            except (ValueError, LookupError), e:
                self._agi.dp_break(str(e))
            else:
                self._agi.set_variable('XIVO_DST_USERNUM', self._line.number)

    def _set_user(self):
        if self._dstid:
            try:
                self._user = objects.User(self._agi, self._cursor, int(self._dstid))
            except (ValueError, LookupError), e:
                self._agi.dp_break(str(e))
            self._set_xivo_user_name()
            self._set_xivo_redirecting_info()

    def _set_xivo_iface(self):
        interface = self._build_interface_from_line(self._line)
        self._agi.set_variable('XIVO_INTERFACE', interface)

    def _build_interface_from_line(self, line):
        protocol = line.protocol
        if protocol.lower() == 'custom':
            interface = line.name
        else:
            interface = '%s/%s' % (protocol, line.name)
        return interface

    def _set_xivo_user_name(self):
        if self._user:
            if self._user.firstname:
                self._agi.set_variable('XIVO_DST_FIRSTNAME', self._user.firstname)
            if self._user.lastname:
                self._agi.set_variable('XIVO_DST_LASTNAME', self._user.lastname)

    def _set_xivo_redirecting_info(self):
        callerid_parsed = CallerID.parse(self._user.callerid)
        if callerid_parsed:
            callerid_name, callerid_num = callerid_parsed
        else:
            callerid_name = None
            callerid_num = None

        if not callerid_name:
            callerid_name = "%s %s" % (self._user.firstname, self._user.lastname)
        self._agi.set_variable('XIVO_DST_REDIRECTING_NAME', callerid_name)

        if not callerid_num:
            if self._line:
                callerid_num = self._line.number
            else:
                callerid_num = self._dstnum
        self._agi.set_variable('XIVO_DST_REDIRECTING_NUM', callerid_num)

    def _call_filtering(self):
        caller = self._caller
        called = self._user

        if called.bsfilter != 'boss':
            return False

        if caller is not None and caller.bsfilter == 'secretary':
            secretary_can_call_boss = callfilter_dao.does_secretary_filter_boss(called.id, caller.id)
            if secretary_can_call_boss:
                return False

        try:
            boss_callfiltermember, callfilter = callfilter_dao.get_by_boss_id(called.id)
        except TypeError:
            return False

        callfilter_active = callfilter_dao.is_activated_by_callfilter_id(boss_callfiltermember.callfilterid)

        if callfilter_active == 0:
            return False

        in_zone = self._callfilter_check_in_zone(callfilter.callfrom)
        if not in_zone is True:
            return False

        secretaries = callfilter_dao.get_secretaries_by_callfiltermember_id(boss_callfiltermember.callfilterid)

        boss_line = self._line
        boss_interface = '%s/%s' % (boss_line.protocol.upper(), boss_line.name)

        if callfilter.bosssecretary in ("bossfirst-simult", "bossfirst-serial", "all"):
            self._agi.set_variable('XIVO_CALLFILTER_BOSS_INTERFACE', boss_interface)
            self._set_callfilter_ringseconds('BOSS_TIMEOUT', boss_callfiltermember.ringseconds)

        index = 0
        ifaces = []
        for secretary in secretaries:
            secretary_callfiltermember, ringseconds = secretary
            if secretary_callfiltermember.active:
                iface = user_line_dao.get_line_identity_by_user_id(secretary_callfiltermember.typeval)
                ifaces.append(iface)

                if callfilter.bosssecretary in ("bossfirst-serial", "secretary-serial"):
                    self._agi.set_variable('XIVO_CALLFILTER_SECRETARY%d_INTERFACE' % index, iface)
                    self._set_callfilter_ringseconds('SECRETARY%d_TIMEOUT' % index, ringseconds)
                    index += 1

        if callfilter.bosssecretary in ("bossfirst-simult", "secretary-simult", "all"):
            self._agi.set_variable('XIVO_CALLFILTER_INTERFACE', '&'.join(ifaces))
            self._set_callfilter_ringseconds('TIMEOUT', callfilter.ringseconds)

        DialAction(self._agi, self._cursor, "noanswer", "callfilter", callfilter.id).set_variables()
        CallerID(self._agi, self._cursor, "callfilter", callfilter.id).rewrite(force_rewrite=True)
        self._agi.set_variable('XIVO_CALLFILTER', '1')
        self._agi.set_variable('XIVO_CALLFILTER_MODE', callfilter.bosssecretary)

        return True

    def _callfilter_check_in_zone(self, callfilter_zone):
        if callfilter_zone == "all":
            return True
        elif callfilter_zone == "internal" and self._zone == "intern":
            return True
        elif callfilter_zone == "external" and self._zone == "extern":
            return True
        else:
            return False

    def _set_mailbox(self):
        mailbox = ""
        mailbox_context = ""
        useremail = ""
        if self._user.vmbox:
            mailbox = self._user.vmbox.mailbox
            mailbox_context = self._user.vmbox.context
            if self._user.vmbox.email:
                useremail = self._user.vmbox.email
        self._agi.set_variable('XIVO_ENABLEVOICEMAIL', self._user.enablevoicemail)
        self._agi.set_variable('XIVO_MAILBOX', mailbox)
        self._agi.set_variable('XIVO_MAILBOX_CONTEXT', mailbox_context)
        self._agi.set_variable('XIVO_USEREMAIL', useremail)

    def _set_vmbox_lang(self):
        vmbox = self._user.vmbox
        if not vmbox:
            return

        mbox_lang = ''
        if self._zone == 'intern' and self._caller and self._caller.language:
            mbox_lang = self._caller.language
        elif vmbox.language:
            mbox_lang = vmbox.language
        elif self._user.language:
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
        self._set_not_zero_or_empty('XIVO_RINGSECONDS', self._user.ringseconds)

    def _set_callfilter_ringseconds(self, name, value):
        self._set_not_zero_or_empty('XIVO_CALLFILTER_%s' % name, value)

    def _set_not_zero_or_empty(self, name, value):
        if value and value > 0:
            self._agi.set_variable(name, value)
        else:
            self._agi.set_variable(name, '')

    def _set_simultcalls(self):
        return self._agi.set_variable('XIVO_SIMULTCALLS', self._user.simultcalls)

    def _set_enablednd(self):
        if self._feature_list.enablednd:
            enablednd = self._user.enablednd
        else:
            enablednd = 0
        self._agi.set_variable('XIVO_ENABLEDND', enablednd)

    def _set_rna_from_dialaction(self):
        return self._set_fwd_from_dialaction('noanswer')

    def _set_rbusy_from_dialaction(self):
        return self._set_fwd_from_dialaction('busy')

    def _set_fwd_from_dialaction(self, forward_type):
        dial_action = objects.DialAction(
            self._agi,
            self._cursor,
            forward_type,
            'user',
            self._user.id,
        )
        dial_action.set_variables()

        return dial_action.action != 'none'

    def _set_rna_from_exten(self, called_line):
        if not self._feature_list.fwdrna or not self._user.enablerna:
            return False

        return self._set_fwd_from_exten('noanswer', called_line, self._user.destrna)

    def _set_rbusy_from_exten(self, called_line):
        if not self._feature_list.fwdbusy or not self._user.enablebusy:
            return False

        return self._set_fwd_from_exten('busy', called_line, self._user.destbusy)

    def _set_fwd_from_exten(self, fwd_type, called_line, dest):
        objects.DialAction.set_agi_variables(
            self._agi,
            fwd_type,
            'user',
            'extension',
            dest,
            called_line.context,
            False,
        )

        return True

    def _setrna(self, called_line):
        if self._set_rna_from_exten(called_line) or self._set_rna_from_dialaction():
            self._agi.set_variable('XIVO_ENABLERNA', True)

    def _setbusy(self, called_line):
        if self._set_rbusy_from_exten(called_line) or self._set_rbusy_from_dialaction():
            self._agi.set_variable('XIVO_ENABLEBUSY', True)

    def _set_enableunc(self, called_line):
        enableunc = 0
        unc_action = 'none'
        unc_actionarg1 = ""
        unc_actionarg2 = ""
        if self._feature_list.fwdunc:
            enableunc = self._user.enableunc
            if enableunc:
                unc_action = 'extension'
                unc_actionarg1 = self._user.destunc
                unc_actionarg2 = called_line.context
        self._agi.set_variable('XIVO_ENABLEUNC', enableunc)
        objects.DialAction.set_agi_variables(self._agi, 'unc', 'user', unc_action, unc_actionarg1, unc_actionarg2, False)

    def _set_call_forwards(self):
        called_line = self._line
        self._set_enableunc(called_line)
        self._setbusy(called_line)
        self._setrna(called_line)

    def _set_dial_action_congestion(self):
        objects.DialAction(self._agi, self._cursor, 'congestion', 'user', self._user.id).set_variables()

    def _set_dial_action_chanunavail(self):
        objects.DialAction(self._agi, self._cursor, 'chanunavail', 'user', self._user.id).set_variables()
