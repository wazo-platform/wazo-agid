# -*- coding: utf-8 -*-
# Copyright 2012-2020 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import time
import requests

from xivo_dao import callfilter_dao, context_dao, user_line_dao as old_user_line_dao

from xivo_dao.resources.user_line import dao as user_line_dao
from xivo_dao.resources.line import dao as line_dao
from xivo_dao.resources.line_extension import dao as line_extension_dao
from xivo_dao.resources.extension import dao as extension_dao

from wazo_agid.helpers import CallRecordingNameGenerator
from wazo_agid.objects import DialAction, CallerID
from wazo_agid.handlers.handler import Handler
from wazo_agid import objects
from wazo_agid import dialplan_variables
from wazo_agid.helpers import is_registered_and_mobile, is_webrtc

logger = logging.getLogger(__name__)


class UserFeatures(Handler):

    PATH_TYPE = 'user'

    def __init__(self, agi, cursor, args):
        Handler.__init__(self, agi, cursor, args)
        self._call_recording_name_generator = CallRecordingNameGenerator(
            agi.config['call_recording']['filename_template'],
            agi.config['call_recording']['filename_extension'],
        )
        self._userid = None
        self._dstid = None
        self._destination_extension_id = None
        self._zone = None
        self._srcnum = None
        self._dstnum = None
        self._feature_list = None
        self._caller = None
        self._user = None

        self.lines = []
        self.main_line = None
        self.main_extension = None

        self.auth_client = agi.config['auth']['client']

    def execute(self):
        self._set_members()
        self._set_interfaces()

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
        self._destination_extension_id = self._agi.get_variable(dialplan_variables.DESTINATION_EXTENSION_ID)
        self._zone = self._agi.get_variable(dialplan_variables.CALL_ORIGIN)
        self._srcnum = self._agi.get_variable(dialplan_variables.SOURCE_NUMBER)
        self._dstnum = self._agi.get_variable(dialplan_variables.DESTINATION_NUMBER)
        self._context = self._agi.get_variable(dialplan_variables.BASE_CONTEXT)
        self._set_caller()
        self._set_line()
        self._set_user()

    def _set_caller(self):
        if self._userid:
            try:
                self._caller = objects.User(self._agi, self._cursor, int(self._userid))
            except (ValueError, LookupError):
                self._caller = None

    def _set_line(self):
        if self._dstid:
            try:
                user_main_line = user_line_dao.get_by(user_id=self._dstid, main_line=True)
                self.main_line = line_dao.find_by(id=user_main_line.line_id)  # XXX Should use get_by

                # destination_extension_id may be unset (e.g. incoming call)
                # In this case, only the main extension of the main line should be rung
                if not self._destination_extension_id:
                    line_extension = line_extension_dao.get_by(line_id=self.main_line.id)  # main_extension=True
                    self._destination_extension_id = line_extension.extension_id

                self.main_extension = extension_dao.get_by(id=self._destination_extension_id)

                line_extensions = line_extension_dao.find_all_by(extension_id=self.main_extension.id)
                for line_extension in line_extensions:
                    line = line_dao.find_by(id=line_extension.line_id)  # XXX Should use get_by
                    self.lines.append(line)

            except (ValueError, LookupError), e:
                self._agi.dp_break(str(e))
            else:
                self._agi.set_variable('XIVO_DST_USERNUM', self.main_extension.exten)
                self._agi.set_variable('WAZO_DST_USER_CONTEXT', self.main_extension.context)

    def _set_user(self):
        if self._dstid:
            try:
                self._user = objects.User(self._agi, self._cursor, int(self._dstid))
            except (ValueError, LookupError), e:
                self._agi.dp_break(str(e))
            self._set_xivo_user_name()
            self._set_xivo_redirecting_info()
            self._set_wazo_uuid()

    def _set_interfaces(self):
        interfaces = [self._build_interface_from_line(line) for line in self.lines]
        self._agi.set_variable('XIVO_INTERFACE', '&'.join(interfaces))

    def _build_interface_from_line(self, line):
        protocol = line.protocol.upper()
        if protocol == 'CUSTOM':
            return self._build_custom_interface(line)
        elif protocol == 'SIP':
            return self._build_sip_interface(line)
        else:
            return self._build_default_interface(line)

    def _build_custom_interface(self, line):
        return line.name

    def _build_default_interface(self, line):
        return '{}/{}'.format(line.protocol.upper(), line.name)

    def _build_sip_interface(self, line):
        if is_webrtc(self._agi, 'PJSIP', line.name):
            if not is_registered_and_mobile(self._agi, line.name):
                # Checking for mobile connections last as this operation does HTTP requests
                if self._has_mobile_connection():
                    self._agi.set_variable('WAZO_WAIT_FOR_MOBILE', 1)
                    return 'Local/{}@wazo_wait_for_registration'.format(line.name)

        default_interface = 'PJSIP/{}'.format(line.name)
        registered_interfaces = self._agi.get_variable('PJSIP_DIAL_CONTACTS({})'.format(line.name))
        return registered_interfaces or default_interface

    def _set_xivo_user_name(self):
        if self._user:
            wazo_dst_name = '{firstname} {lastname}'.format(
                firstname=self._user.firstname if self._user.firstname else '',
                lastname=self._user.lastname if self._user.lastname else '',
            )
            self._agi.set_variable('WAZO_DST_NAME', wazo_dst_name.strip())

    def _set_wazo_uuid(self):
        if self._user:
            self._agi.set_variable('WAZO_DST_UUID', self._user.uuid)
            self._agi.set_variable('WAZO_DST_TENANT_UUID', self._user.tenant_uuid)

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
            if self.main_extension:
                callerid_num = self.main_extension.exten
            else:
                callerid_num = self._dstnum
        self._agi.set_variable('XIVO_DST_REDIRECTING_NUM', callerid_num)

    def _call_filtering(self):
        caller = self._caller
        called = self._user

        boss_callfiltermember = callfilter_dao.find_boss(called.id)
        if not boss_callfiltermember:
            logger.debug('Ignoring callfilter: No boss')
            return False

        if caller is not None:
            secretary_can_call_boss = callfilter_dao.does_secretary_filter_boss(called.id, caller.id)
            if secretary_can_call_boss:
                logger.debug('Ignoring callfilter: secretary can call boss')
                return False

        callfilter = callfilter_dao.find(boss_callfiltermember.callfilterid)
        if not callfilter:
            logger.debug('Ignoring callfilter: no such callfilter: "%s"', boss_callfiltermember.callfilterid)
            return False

        callfilter_active = callfilter_dao.is_activated_by_callfilter_id(boss_callfiltermember.callfilterid)

        if callfilter_active == 0:
            logger.debug('Ignoring callfilter: callfilter is not active')
            return False

        in_zone = self._callfilter_check_in_zone(callfilter.callfrom)
        if in_zone is not True:
            logger.debug('Ignoring callfilter: call not in zone')
            return False

        secretaries = callfilter_dao.get_secretaries_by_callfiltermember_id(boss_callfiltermember.callfilterid)

        boss_line = self.main_line
        protocol = boss_line.protocol.upper()
        # TODO PJSIP migration
        if protocol.startswith('SIP'):
            protocol = 'PJ{}'.format(protocol)
        boss_interface = '{}/{}'.format(protocol, boss_line.name)

        if callfilter.bosssecretary in ("bossfirst-simult", "bossfirst-serial", "all"):
            self._agi.set_variable('XIVO_CALLFILTER_BOSS_INTERFACE', boss_interface)
            self._set_callfilter_ringseconds('BOSS_TIMEOUT', boss_callfiltermember.ringseconds)

        index = 0
        ifaces = []
        for secretary in secretaries:
            secretary_callfiltermember, ringseconds = secretary
            if secretary_callfiltermember.active:
                iface = old_user_line_dao.get_line_identity_by_user_id(secretary_callfiltermember.typeval)
                # TODO PJSIP migration
                if iface.startswith('SIP'):
                    iface = 'PJ{}'.format(iface)
                if iface.startswith('sip'):
                    iface = 'pj{}'.format(iface)
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
        callrecordfile = self._build_call_record_file_name() or ''
        self._agi.set_variable('XIVO_CALLRECORDFILE', callrecordfile)

    def _build_call_record_file_name(self):
        should_record = self._user.callrecord or (self._caller and self._caller.callrecord)
        if not should_record:
            return

        args = {
            'srcnum': self._srcnum,
            'dstnum': self._dstnum,
            'timestamp': int(time.time()),
            'local_time': time.asctime(time.localtime()),
            'utc_time': time.asctime(time.gmtime()),
            'base_context': self._context,
            'tenant_uuid': context_dao.get(self._context).tenant_uuid,
        }
        return self._call_recording_name_generator.generate(args)

    def _set_music_on_hold(self):
        if self._user.musiconhold:
            self._agi.set_variable('CHANNEL(musicclass)', self._user.musiconhold)

    def _set_options(self):
        options = ''
        if self._user.dtmf_hangup:
            options += "h"
        if self._caller and self._caller.dtmf_hangup:
            options += "H"
        if self._user.enablexfer:
            options += "t"
        if self._caller and self._caller.enablexfer:
            options += "T"
        if self._user.enableonlinerec:
            options += "x"
        if self._caller and self._caller.enableonlinerec:
            options += "X"
        if self._user.incallfilter:
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
        self._agi.set_variable('XIVO_ENABLEDND', self._user.enablednd)

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

    def _set_rna_from_exten(self):
        if not self._user.enablerna:
            return False

        return self._set_fwd_from_exten('noanswer', self.main_extension.context, self._user.destrna)

    def _set_rbusy_from_exten(self):
        if not self._user.enablebusy:
            return False

        return self._set_fwd_from_exten('busy', self.main_extension.context, self._user.destbusy)

    def _set_fwd_from_exten(self, fwd_type, context, dest):
        objects.DialAction.set_agi_variables(
            self._agi,
            fwd_type,
            'user',
            'extension',
            dest,
            context,
            False,
        )

        return True

    def _setrna(self):
        if self._set_rna_from_exten() or self._set_rna_from_dialaction():
            self._agi.set_variable('XIVO_ENABLERNA', True)

    def _setbusy(self):
        if self._set_rbusy_from_exten() or self._set_rbusy_from_dialaction():
            self._agi.set_variable('XIVO_ENABLEBUSY', True)

    def _set_enableunc(self):
        if self._user.enableunc:
            unc_action = 'extension'
            unc_actionarg1 = self._user.destunc
            unc_actionarg2 = self.main_extension.context
        else:
            unc_action = 'none'
            unc_actionarg1 = ""
            unc_actionarg2 = ""
        self._agi.set_variable('XIVO_ENABLEUNC', self._user.enableunc)
        objects.DialAction.set_agi_variables(self._agi, 'unc', 'user', unc_action, unc_actionarg1, unc_actionarg2, False)

    def _set_call_forwards(self):
        self._set_enableunc()
        self._setbusy()
        self._setrna()

    def _set_dial_action_congestion(self):
        objects.DialAction(self._agi, self._cursor, 'congestion', 'user', self._user.id).set_variables()

    def _set_dial_action_chanunavail(self):
        objects.DialAction(self._agi, self._cursor, 'chanunavail', 'user', self._user.id).set_variables()

    def _has_mobile_connection(self):
        mobile = False

        try:
            response = self.auth_client.token.list(self._user.uuid, mobile=True)
        except requests.HTTPError as e:
            self._agi.verbose('failed to fetch user refresh tokens {}'.format(e))
        else:
            mobile = response['filtered'] > 0

        if not mobile:
            try:
                response = self.auth_client.users.get_sessions(self._user.uuid)
            except requests.HTTPError as e:
                self._agi.verbose('failed to fetch user sessions {}'.format(e))
            else:
                for session in response['items']:
                    if session['mobile']:
                        mobile = True
                        break

        if mobile:
            self._agi.set_variable('WAZO_MOBILE_CONNECTION', True)
            return True

        return False
