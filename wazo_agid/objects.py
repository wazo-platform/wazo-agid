# -*- coding: utf-8 -*-
# Copyright 2007-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import re
import time
from wazo_agid.schedule import ScheduleAction, SchedulePeriodBuilder, Schedule, \
    AlwaysOpenedSchedule

from xivo_dao import user_dao

logger = logging.getLogger(__name__)


class UnknownUser(Exception):
    pass


class DBUpdateException(Exception):
    pass


class ExtenFeatures(object):
    FEATURES = {
        'agents': (('agentstaticlogin',),
                   ('agentstaticlogoff',),
                   ('agentstaticlogtoggle',)),

        'forwards': (('fwdbusy', 'busy'),
                     ('fwdrna', 'rna'),
                     ('fwdunc', 'unc')),

        'groupmember': (('groupmemberjoin',),
                        ('groupmemberleave',),
                        ('groupmembertoggle',)),

        'services': (('enablevm', 'enablevoicemail'),
                     ('callrecord', 'callrecord'),
                     ('incallfilter', 'incallfilter'),
                     ('enablednd', 'enablednd'))}

    def __init__(self, agi, cursor):
        self.agi = agi
        self.cursor = cursor

        featureslist = []

        for xtype in self.FEATURES.itervalues():
            for x in xtype:
                featureslist.append(x[0])

        self.featureslist = tuple(featureslist)

        self.cursor.query("SELECT ${columns} FROM extensions "
                          "WHERE typeval IN (" + ", ".join(["%s"] * len(self.featureslist)) + ") "
                          "AND commented = 0",
                          ('typeval',),
                          self.featureslist)
        res = self.cursor.fetchall()

        if not res:
            enabled_features = []
        else:
            enabled_features = [row['typeval'] for row in res]

        for feature in self.featureslist:
            setattr(self, feature, (feature in enabled_features))

    def get_name_by_exten(self, exten):
        self.cursor.query("SELECT ${columns} FROM extensions "
                          "WHERE typeval IN (" + ", ".join(["%s"] * len(self.featureslist)) + ") "
                          "AND (exten = %s "
                          "OR (SUBSTR(exten,1,1) = '_' "
                          "    AND SUBSTR(exten, 2, %s) LIKE %s)) "
                          "AND commented = 0",
                          ('typeval',),
                          self.featureslist + (exten, len(exten), "%s%%" % exten))

        res = self.cursor.fetchone()

        if not res:
            raise LookupError("Unable to find feature by exten (exten = %r)" % exten)

        return res['typeval']

    def get_exten_by_name(self, name, commented=None):
        query = "SELECT ${columns} FROM extensions WHERE typeval = %s"
        params = [name]

        if commented is not None:
            params.append(int(bool(commented)))
            query += " AND commented = %s"

        self.cursor.query(query, ('exten',), params)

        res = self.cursor.fetchone()

        if not res:
            raise LookupError("Unable to find feature by name (name = %r)" % name)

        return res['exten']


class VMBox(object):
    def __init__(self, agi, cursor, xid=None, mailbox=None, context=None, commentcond=True):
        self.agi = agi
        self.cursor = cursor

        vm_columns = ('uniqueid', 'mailbox', 'context', 'password', 'email', 'commented', 'language', 'skipcheckpass')
        columns = ["voicemail." + c for c in vm_columns]

        if commentcond:
            where_comment = "AND voicemail.commented = 0"
        else:
            where_comment = ""

        if xid:
            cursor.query("SELECT ${columns} FROM voicemail "
                         "WHERE voicemail.uniqueid = %s " +
                         where_comment,
                         columns,
                         (xid,))
        elif mailbox and context:
            contextinclude = Context(agi, cursor, context).include
            cursor.query("SELECT ${columns} FROM voicemail "
                         "WHERE voicemail.mailbox = %s "
                         "AND voicemail.context IN (" + ", ".join(["%s"] * len(contextinclude)) + ") " +
                         where_comment,
                         columns,
                         [mailbox] + contextinclude)
        else:
            raise LookupError("id or mailbox@context must be provided to look up a voicemail entry")

        res = cursor.fetchone()

        if not res:
            raise LookupError("Unable to find voicemail box (id: %s, mailbox: %s, context: %s)" % (xid, mailbox, context))

        self.id = res['voicemail.uniqueid']
        self.mailbox = res['voicemail.mailbox']
        self.context = res['voicemail.context']
        self.password = res['voicemail.password']
        self.email = res['voicemail.email']
        self.commented = res['voicemail.commented']
        self.language = res['voicemail.language']
        self.skipcheckpass = res['voicemail.skipcheckpass']

    def toggle_enable(self, enabled=None):
        if enabled is None:
            enabled = int(not self.commented)
        else:
            enabled = int(not bool(enabled))

        self.cursor.query("UPDATE voicemail "
                          "SET commented = %s "
                          "WHERE uniqueid = %s",
                          parameters=(enabled, self.id))

        if self.cursor.rowcount != 1:
            raise DBUpdateException("Unable to perform the requested update")
        else:
            self.commented = enabled


class Paging(object):

    def __init__(self, agi, cursor, number, userid):
        self.agi = agi
        self.cursor = cursor
        self.lines = set()

        columns = ('id','number', 'duplex', 'ignore', 'record', 'quiet', 'timeout', 'announcement_file', 'announcement_play', 'announcement_caller', 'commented', 'tenant_uuid')

        cursor.query("SELECT ${columns} FROM paging "
                     "WHERE number = %s "
                     "AND commented = 0",
                     columns,
                     (number,))
        res = cursor.fetchone()

        if not res:
            raise LookupError("Unable to find paging entry (number: %s)" % (number,))

        id = res['id']
        self.tenant_uuid = res['tenant_uuid']
        self.number = res['number']
        self.duplex = res['duplex']
        self.ignore = res['ignore']
        self.record = res['record']
        self.quiet = res['quiet']
        self.timeout = res['timeout']
        self.announcement_file = res['announcement_file']
        self.announcement_play = res['announcement_play']
        self.announcement_caller = res['announcement_caller']

        columns = ('userfeaturesid',)

        cursor.query("SELECT ${columns} FROM paginguser "
                     "WHERE userfeaturesid = %s AND pagingid = %s "
                     "AND caller = 1",
                     columns,
                     (userid, id))
        res = cursor.fetchone()

        if not res:
            raise LookupError("Unable to find paging caller entry (userfeaturesid: %s)" % (userid,))

        columns = ('endpoint_sip_uuid', 'endpoint_sccp_id', 'endpoint_custom_id', 'name')

        cursor.query("SELECT ${columns} FROM paginguser "
                     "JOIN user_line ON paginguser.userfeaturesid = user_line.user_id "
                     "JOIN linefeatures ON user_line.line_id = linefeatures.id "
                     "WHERE paginguser.pagingid = %s "
                     "AND paginguser.caller = 0",
                     columns,
                     (id,))
        res = cursor.fetchall()

        if not res:
            raise LookupError("Unable to find paging users entry (id: %s)" % (id,))

        for l in res:
            if l['endpoint_sip_uuid']:
                line = 'SIP/{}'.format(l['name'])
            elif l['endpoint_sccp_id']:
                line = 'SCCP/{}/autoanswer'.format(l['name'])
            elif l['endpoint_custom_id']:
                line = 'CUSTOM/{}'.format(l['name'])
            else:
                raise LookupError("Unable to find protocol for user (id: %s)" % (id,))

            self.lines.add(line)


class UserLine:

    def __init__(self, agi, user_uuid):
        self._agi = agi
        self.interfaces = []
        hint = agi.get_variable('HINT({}@usersharedlines)'.format(user_uuid))
        if not hint:
            raise UnknownUser()

        for endpoint in hint.split('&'):
            if '/' not in endpoint:
                continue

            for interface in self._find_matching_interfaces(endpoint):
                self.interfaces.append(interface)

    def _find_matching_interfaces(self, endpoint):
        protocol, name = endpoint.split('/', 1)
        if protocol == 'pjsip':
            contacts = self._agi.get_variable('PJSIP_DIAL_CONTACTS({name})'.format(name=name))
            if not contacts:
                return

            for contact in contacts.split('&'):
                yield contact
        else:
            yield endpoint


class User(object):

    def __init__(self, agi, cursor, xid=None, exten=None, context=None):
        self.agi = agi
        self.cursor = cursor

        if xid:
            user_row = user_dao.get(xid)
        elif exten and context:
            user_row = user_dao.get_user_by_number_context(exten, context)
        else:
            raise LookupError("id or exten@context must be provided to look up an user entry")

        self.id = user_row.id
        self.uuid = user_row.uuid
        self.tenant_uuid = user_row.tenant_uuid
        self.firstname = user_row.firstname
        self.lastname = user_row.lastname
        self.language = user_row.language
        self.userfield = user_row.userfield
        self.callerid = user_row.callerid
        self.mobilephonenumber = user_row.mobilephonenumber
        self.musiconhold = user_row.musiconhold
        self.outcallerid = user_row.outcallerid
        self.ringseconds = int(user_row.ringseconds)
        self.simultcalls = user_row.simultcalls
        self.enablevoicemail = user_row.enablevoicemail
        self.voicemailid = user_row.voicemailid
        self.enablexfer = user_row.enablexfer
        self.dtmf_hangup = user_row.dtmf_hangup
        self.enableonlinerec = user_row.enableonlinerec
        self.callrecord = user_row.callrecord
        self.incallfilter = user_row.incallfilter
        self.enablednd = user_row.enablednd
        self.enableunc = user_row.enableunc
        self.destunc = user_row.destunc
        self.enablerna = user_row.enablerna
        self.destrna = user_row.destrna
        self.enablebusy = user_row.enablebusy
        self.destbusy = user_row.destbusy
        self.preprocess_subroutine = user_row.preprocess_subroutine
        self.bsfilter = user_row.bsfilter
        self.rightcallcode = user_row.rightcallcode

        if self.destunc == '':
            self.enableunc = 0

        if self.destrna == '':
            self.enablerna = 0

        if self.destbusy == '':
            self.enablebusy = 0

        self.vmbox = None
        if self.enablevoicemail and self.voicemailid:
            try:
                self.vmbox = VMBox(agi, cursor, self.voicemailid)
            except LookupError:
                self.vmbox = None

        if not self.vmbox:
            self.enablevoicemail = 0

    def toggle_feature(self, feature):
        if feature not in ("enablevoicemail", "callrecord"):
            raise ValueError("invalid feature")

        enabled = int(not getattr(self, feature))

        self.cursor.query("UPDATE userfeatures "
                          "SET %s = %%s "
                          "WHERE id = %%s" % feature,
                          parameters=(enabled, self.id))

        if self.cursor.rowcount != 1:
            raise DBUpdateException("Unable to perform the requested update")
        else:
            setattr(self, feature, enabled)


class MeetMe(object):

    OPTIONS_GLOBAL = {'talkeroptimization': '',  # Disabled
                      'record': 'r',
                      'talkerdetection': '',  # Disabled
                      'noplaymsgfirstenter': '1',
                      'closeconfdurationexceeded': 'L'}

    OPTIONS_COMMON = {'mode': {'listen': 'l',
                               'talk': 't',
                               'all': ''},
                      'announceusercount': 'c',
                      'announcejoinleave': {'no': '',
                                            'yes': 'i',
                                            'noreview': 'I'},
                      'initiallymuted': 'm',
                      'musiconhold': 'M',
                      'poundexit': 'p',
                      'quiet': 'q',
                      'starmenu': 's',
                      'enableexitcontext': 'X'}

    OPTIONS_ADMIN = {'moderationmode': 'k',
                     'closeconflastmarkedexit': 'x'}

    OPTIONS_USER = {'hiddencalls': 'h'}

    def __init__(self, agi, cursor, xid):
        self.agi = agi
        self.cursor = cursor

        meetmefeatures_columns = (('id', 'name', 'confno', 'context',
                                   'admin_typefrom', 'admin_internalid', 'admin_externalid',
                                   'admin_identification', 'admin_exitcontext') +
                                  tuple(["admin_%s" % x for x in (self.OPTIONS_COMMON.keys() +
                                                                  self.OPTIONS_ADMIN.keys())]) +
                                  ('user_exitcontext',) +
                                  tuple(["user_%s" % x for x in (self.OPTIONS_COMMON.keys() +
                                                                 self.OPTIONS_USER.keys())]) +
                                  tuple(x for x in self.OPTIONS_GLOBAL.keys()) +
                                  ('durationm', 'nbuserstartdeductduration',
                                   'timeannounceclose', 'maxusers',
                                   'startdate', 'preprocess_subroutine'))

        columns = ["meetmefeatures." + c for c in meetmefeatures_columns] + \
                  ['staticmeetme.var_val'] + \
                  ['extensions.exten']

        cursor.query("SELECT ${columns} FROM meetmefeatures "
                     "INNER JOIN staticmeetme "
                     "ON meetmefeatures.meetmeid = staticmeetme.id "
                     "LEFT JOIN user_line "
                     "ON meetmefeatures.admin_internalid = user_line.user_id "
                     "LEFT JOIN extensions "
                     "ON extensions.type = 'user' AND user_line.line_id = CAST(extensions.typeval AS integer)"
                     "WHERE meetmefeatures.id = %s "
                     "AND staticmeetme.commented = 0",
                     columns,
                     (xid,))

        res = cursor.fetchone()

        if not res:
            raise LookupError("Unable to find conference room (id: %s)" % xid)

        (self.confno, self.pin, self.pinadmin) = (res['staticmeetme.var_val'] + ",,").split(',', 3)[:3]
        self.admin_number = res['extensions.exten']

        if res['meetmefeatures.startdate']:
            self.starttime = time.mktime(
                time.strptime(res['meetmefeatures.startdate'],
                              '%Y-%m-%d %H:%M:%S'))
        else:
            self.starttime = None

        for name, value in res.iteritems():
            if name not in('staticmeetme.var_val', 'extensions.exten'):
                setattr(self, name.split('.', 1)[1], value)

        self.options = ()

    def _get_options(self, xdict, prefix=None):
        options = set()

        for name, opt in xdict.iteritems():
            if prefix:
                name = prefix + name

            attrvalue = getattr(self, name)

            if not attrvalue:
                continue
            elif isinstance(opt, dict):
                options.add(opt[attrvalue])
            elif isinstance(opt, basestring):
                options.add(opt)
            else:
                raise TypeError("Invalid type for option: %r" % opt)

        return options

    def get_global_options(self):
        options = self._get_options(self.OPTIONS_GLOBAL.copy())

        if self.OPTIONS_GLOBAL['closeconfdurationexceeded'] in options:
            options.remove(self.OPTIONS_GLOBAL['closeconfdurationexceeded'])
            if self.durationm:
                opt = [str(int(self.durationm) * 60)]

                if self.nbuserstartdeductduration:
                    opt.append(str(self.nbuserstartdeductduration))
                else:
                    opt.append("")

                if self.timeannounceclose:
                    opt.append(str(self.timeannounceclose))

                options.add("%s(%s)" % (self.OPTIONS_GLOBAL['closeconfdurationexceeded'],
                                        "|".join(opt).rstrip("|")))

        return set(options)

    def get_user_options(self):
        user_options = self.OPTIONS_COMMON.copy()
        user_options.update(self.OPTIONS_USER)
        options = self._get_options(user_options, "user_")

        if self.admin_moderationmode:
            options.add(self.OPTIONS_ADMIN['moderationmode'])

        if self.OPTIONS_COMMON['enableexitcontext'] in options \
                and not self.user_exitcontext:
            options.remove(self.OPTIONS_COMMON['enableexitcontext'])

        return set(options)

    def get_user_option(self, option):
        return getattr(self, "user_%s" % option)


class Queue(object):
    def __init__(self, agi, cursor, xid=None, number=None, context=None):
        self.agi = agi
        self.cursor = cursor

        queuefeatures_columns = [
            'id', 'tenant_uuid', 'number', 'context', 'name', 'data_quality',
            'hitting_callee', 'hitting_caller', 'retries', 'ring',
            'transfer_user', 'transfer_call', 'write_caller',
            'write_calling', 'ignore_forward', 'url', 'announceoverride', 'timeout',
            'preprocess_subroutine', 'announce_holdtime', 'waittime',
            'waitratio', 'mark_answered_elsewhere'
        ]
        queuefeatures_columns = ["queuefeatures." + c for c in queuefeatures_columns]
        queue_columns = ['queue.wrapuptime', 'queue.musicclass']

        columns = queuefeatures_columns + queue_columns

        if xid:
            cursor.query("SELECT ${columns} FROM queuefeatures "
                         "INNER JOIN queue "
                         "ON queuefeatures.name = queue.name "
                         "WHERE queuefeatures.id = %s "
                         "AND queue.commented = 0 "
                         "AND queue.category = 'queue'",
                         columns,
                         (xid,))
        elif number and context:
            contextinclude = Context(agi, cursor, context).include
            cursor.query("SELECT ${columns} FROM queuefeatures "
                         "INNER JOIN queue "
                         "ON queuefeatures.name = queue.name "
                         "WHERE queuefeatures.number = %s "
                         "AND queuefeatures.context IN (" + ", ".join(["%s"] * len(contextinclude)) + ") "
                         "AND queue.commented = 0 "
                         "AND queue.category = 'queue'",
                         columns,
                         [number] + contextinclude)
        else:
            raise LookupError("id or number@context must be provided to look up a queue")

        res = cursor.fetchone()

        if not res:
            raise LookupError("Unable to find queue (id: %s, number: %s, context: %s)" % (xid, number, context))

        self.id = res['queuefeatures.id']
        self.tenant_uuid = res['queuefeatures.tenant_uuid']
        self.number = res['queuefeatures.number']
        self.context = res['queuefeatures.context']
        self.name = res['queuefeatures.name']
        self.data_quality = res['queuefeatures.data_quality']
        self.hitting_callee = res['queuefeatures.hitting_callee']
        self.hitting_caller = res['queuefeatures.hitting_caller']
        self.retries = res['queuefeatures.retries']
        self.ring = res['queuefeatures.ring']
        self.transfer_user = res['queuefeatures.transfer_user']
        self.transfer_call = res['queuefeatures.transfer_call']
        self.write_caller = res['queuefeatures.write_caller']
        self.write_calling = res['queuefeatures.write_calling']
        self.ignore_forward = res['queuefeatures.ignore_forward']
        self.url = res['queuefeatures.url']
        self.announceoverride = res['queuefeatures.announceoverride']
        self.timeout = res['queuefeatures.timeout']
        self.preprocess_subroutine = res['queuefeatures.preprocess_subroutine']
        self.announce_holdtime = res['queuefeatures.announce_holdtime']
        self.waittime = res['queuefeatures.waittime']
        self.waitratio = res['queuefeatures.waitratio']
        self.wrapuptime = res['queue.wrapuptime']
        self.musiconhold = res['queue.musicclass']
        self.mark_answered_elsewhere = res['queuefeatures.mark_answered_elsewhere']

    def set_dial_actions(self):
        for event in ['congestion', 'busy', 'chanunavail', 'qwaittime', 'qwaitratio']:
            DialAction(self.agi, self.cursor, event, "queue", self.id).set_variables()

        # case NOANSWER (timeout): we also set correct queuelog event
        action = DialAction(self.agi, self.cursor, 'noanswer', "queue", self.id)
        action.set_variables()
        if action.action in ['voicemail', 'sound']:
            self.agi.set_variable("XIVO_QUEUELOG_EVENT", "REROUTEGUIDE")

    def rewrite_cid(self):
        CallerID(self.agi, self.cursor, "queue", self.id).rewrite(force_rewrite=False)

    def pickupgroups(self):
        self.cursor.query(
            "SELECT ${columns} FROM pickup p, pickupmember pm "
            "WHERE p.commented = 0 AND p.id = pm.pickupid "
            "AND pm.category = 'member' AND pm.membertype = 'queue'"
            "AND pm.memberid = %s",
            ('p.id',), (self.id,)
        )

        res = self.cursor.fetchall()
        if res is None:
            raise LookupError("Unable to fetch queue %s pickupgroups" % (self.id))

        return [str(row[0]) for row in res]


class Agent(object):
    def __init__(self, agi, cursor, xid=None, number=None):
        self.agi = agi
        self.cursor = cursor

        columns = ('id', 'tenant_uuid', 'number', 'passwd', 'firstname', 'lastname', 'language', 'preprocess_subroutine')

        if xid:
            cursor.query("SELECT ${columns} FROM agentfeatures "
                         "WHERE id = %s ",
                         columns,
                         (xid,))
        elif number:
            cursor.query("SELECT ${columns} FROM agentfeatures "
                         "WHERE number = %s ",
                         columns,
                         (number,))
        else:
            raise LookupError("id or number must be provided to look up an agent")

        res = cursor.fetchone()

        if not res:
            raise LookupError("Unable to find agent (id: %s, number: %s)" % (xid, number))

        self.id = res['id']
        self.tenant_uuid = res['tenant_uuid']
        self.number = res['number']
        self.passwd = res['passwd']
        self.firstname = res['firstname']
        self.lastname = res['lastname']
        self.language = res['language']
        self.preprocess_subroutine = res['preprocess_subroutine']


class DialAction(object):

    @staticmethod
    def set_agi_variables(agi, event, category, action, actionarg1, actionarg2, isda=True):
        xtype = ("%s_%s" % (category, event)).upper()
        agi.set_variable("XIVO_FWD_%s_ACTION" % xtype, action)

        # Sometimes, it's useful to know whether these variables were
        # set manually, or by this object.
        if isda:
            agi.set_variable("XIVO_FWD_%s_ISDA" % xtype, "1")

        if actionarg1:
            actionarg1 = actionarg1.replace('|', ';')
        else:
            actionarg1 = ""

        if actionarg2:
            actionarg2 = actionarg2
        else:
            actionarg2 = ""

        agi.set_variable("XIVO_FWD_%s_ACTIONARG1" % xtype,
                         actionarg1)
        agi.set_variable("XIVO_FWD_%s_ACTIONARG2" % xtype,
                         actionarg2)

    def __init__(self, agi, cursor, event, category, categoryval):
        self.agi = agi
        self.cursor = cursor
        self.event = event
        self.category = category

        cursor.query("SELECT ${columns} FROM dialaction "
                     "WHERE event = %s "
                     "AND category = %s "
                     "AND " + cursor.cast('categoryval', 'int') + " = %s ",
                     ('action', 'actionarg1', 'actionarg2'),
                     (event, category, categoryval))
        res = cursor.fetchone()

        if not res:
            self.action = "none"
            self.actionarg1 = None
            self.actionarg2 = None
        else:
            self.action = res['action']
            self.actionarg1 = res['actionarg1']
            self.actionarg2 = res['actionarg2']

    def set_variables(self):
        category_no_isda = ('none',
                            'endcall:busy',
                            'endcall:congestion',
                            'endcall:hangup')

        DialAction.set_agi_variables(self.agi,
                                     self.event,
                                     self.category,
                                     self.action,
                                     self.actionarg1,
                                     self.actionarg2,
                                     (self.category not in category_no_isda))


class Trunk(object):
    def __init__(self, agi, cursor, xid):
        self.agi = agi
        self.cursor = cursor

        columns = ('endpoint_sip_uuid', 'endpoint_iax_id', 'endpoint_custom_id')

        cursor.query("SELECT ${columns} FROM trunkfeatures "
                     "WHERE id = %s",
                     columns,
                     (xid,))
        res = cursor.fetchone()
        self.agi.verbose('res {}'.format(res))

        if not res:
            raise LookupError("Unable to find trunk (id: %d)" % xid)

        self.id = xid

        if res['endpoint_sip_uuid']:
            (self.interface, self.intfsuffix) = ChanSIP.get_intf_and_suffix(cursor, res['endpoint_sip_uuid'])
        elif res['endpoint_iax_id']:
            (self.interface, self.intfsuffix) = ChanIAX2.get_intf_and_suffix(cursor, res['endpoint_iax_id'])
        elif res['endpoint_custom_id']:
            (self.interface, self.intfsuffix) = ChanCustom.get_intf_and_suffix(cursor, res['endpoint_custom_id'])
        else:
            raise ValueError("Unknown protocol for trunk {}".format(xid))


class DID(object):
    def __init__(self, agi, cursor, xid=None, exten=None, context=None):
        self.agi = agi
        self.cursor = cursor

        columns = (
            'incall.id',
            'incall.preprocess_subroutine',
            'incall.greeting_sound',
            'extensions.exten',
            'extensions.context',
        )

        if xid:
            cursor.query(
                "SELECT ${columns} FROM incall "
                "JOIN extensions ON extensions.type = 'incall' "
                "AND extensions.typeval = CAST(incall.id AS VARCHAR(255)) "
                "WHERE incall.id = %s "
                "AND incall.commented = 0 AND extensions.commented = 0",
                columns,
                (xid,),
            )
        elif exten and context:
            contextinclude = Context(agi, cursor, context).include
            cursor.query(
                "SELECT ${columns} FROM incall "
                "JOIN extensions ON extensions.type = 'incall' "
                "AND extensions.typeval = CAST(incall.id AS VARCHAR(255)) "
                "WHERE extensions.exten = %s "
                "AND extensions.context IN (%s) "
                "AND incall.commented = 0 AND extensions.commented = 0",
                columns,
                (exten, ','.join(contextinclude)),
            )
        else:
            raise LookupError("id or exten@context must be provided to look up a DID entry")

        res = cursor.fetchone()

        if not res:
            raise LookupError("Unable to find DID entry (id: %s, exten: %s, context: %s)" % (xid, exten, context))

        self.id = res['incall.id']
        self.exten = res['extensions.exten']
        self.context = res['extensions.context']
        self.preprocess_subroutine = res['incall.preprocess_subroutine']
        self.greeting_sound = res['incall.greeting_sound']

    def set_dial_actions(self):
        DialAction(self.agi, self.cursor, "answer", "incall", self.id).set_variables()

    def rewrite_cid(self):
        CallerID(self.agi, self.cursor, "incall", self.id).rewrite(force_rewrite=True)


class Outcall(object):
    def __init__(self, agi, cursor):
        self.agi = agi
        self.cursor = cursor

    def retrieve_values(self, dialpattern_id):
        columns = ('outcall.name', 'outcall.context', 'outcall.internal',
                   'outcall.preprocess_subroutine', 'outcall.hangupringtime', 'outcall.commented',
                   'outcall.id', 'dialpattern.typeid', 'dialpattern.type', 'dialpattern.exten',
                   'dialpattern.stripnum', 'dialpattern.externprefix',
                   'dialpattern.callerid', 'dialpattern.prefix')

        if dialpattern_id:
            self.cursor.query("SELECT ${columns} FROM outcall, dialpattern "
                              "WHERE dialpattern.typeid = outcall.id "
                              "AND dialpattern.type = 'outcall' "
                              "AND dialpattern.id = %s"
                              "AND outcall.commented = 0",
                              columns,
                              (dialpattern_id,))
        else:
            raise LookupError("id or exten@context must be provided to look up an outcall entry")

        res = self.cursor.fetchone()

        if not res:
            raise LookupError("Unable to find outcall entry (id: %s)" % dialpattern_id)

        self.id = res['outcall.id']
        self.exten = res['dialpattern.exten']
        self.context = res['outcall.context']
        self.externprefix = res['dialpattern.externprefix']
        self.stripnum = res['dialpattern.stripnum']
        self.callerid = res['dialpattern.callerid']
        self.internal = res['outcall.internal']
        self.preprocess_subroutine = res['outcall.preprocess_subroutine']
        self.hangupringtime = res['outcall.hangupringtime']

        self.cursor.query("SELECT ${columns} FROM outcalltrunk "
                          "WHERE outcallid = %s "
                          "ORDER BY priority ASC",
                          ('trunkfeaturesid',),
                          (self.id,))
        res = self.cursor.fetchall()

        if not res:
            raise ValueError("No trunk associated with outcall (id: %d)" % dialpattern_id)

        self.trunks = []

        for row in res:
            try:
                trunk = Trunk(self.agi, self.cursor, row['trunkfeaturesid'])
            except LookupError:
                continue

            self.trunks.append(trunk)


class ScheduleDataMapper(object):
    @classmethod
    def get_from_path(cls, cursor, path, path_id):
        # fetch schedule info
        columns = ('id', 'timezone', 'fallback_action', 'fallback_actionid', 'fallback_actionargs')
        cursor.query("SELECT ${columns} FROM schedule_path p "
                     "LEFT JOIN schedule s ON p.schedule_id = s.id "
                     "WHERE p.path = %s "
                     "AND p.pathid = %s "
                     "AND s.commented = 0",
                     columns,
                     (path, path_id))
        res = cursor.fetchone()

        if not res:
            return AlwaysOpenedSchedule()

        schedule_id = res['id']
        timezone = res['timezone']
        if not timezone:
            columns = ('timezone',)
            cursor.query("SELECT ${columns} FROM infos", columns)
            infos = cursor.fetchone()
            timezone = infos['timezone']

        default_action = ScheduleAction(res['fallback_action'],
                                        res['fallback_actionid'],
                                        res['fallback_actionargs'])

        # fetch schedule periods
        columns = ('mode', 'hours', 'weekdays', 'monthdays', 'months', 'action', 'actionid', 'actionargs')
        cursor.query("SELECT ${columns} FROM schedule_time "
                     "WHERE schedule_id = %s",
                     columns,
                     (schedule_id,))
        res = cursor.fetchall()

        opened_periods = []
        closed_periods = []
        for res_period in res:
            period_builder = SchedulePeriodBuilder()
            period_builder.hours(res_period['hours'])
            period_builder.weekdays(res_period['weekdays'])
            period_builder.days(res_period['monthdays'])
            period_builder.months(res_period['months'])

            if res_period['mode'] == 'opened':
                opened_periods.append(period_builder.build())
            else:
                action = ScheduleAction(res_period['action'],
                                        res_period['actionid'],
                                        res_period['actionargs'])
                period_builder.action(action)
                closed_periods.append(period_builder.build())

        return Schedule(opened_periods, closed_periods, default_action, timezone)


class Context(object):
    # TODO: Recursive inclusion
    def __init__(self, agi, cursor, context):
        self.agi = agi
        self.cursor = cursor

        columns = ('context.name', 'context.displayname',
                   'contextinclude.include')

        cursor.query("SELECT ${columns} FROM context "
                     "LEFT JOIN contextinclude "
                     "ON context.name = contextinclude.context "
                     "LEFT JOIN context AS contextinc "
                     "ON contextinclude.include = contextinc.name "
                     "AND context.commented = contextinc.commented "
                     "WHERE context.name = %s "
                     "AND context.commented = 0 "
                     "AND (contextinclude.include IS NULL "
                     "     OR contextinc.name IS NOT NULL) "
                     "ORDER BY contextinclude.priority ASC",
                     columns,
                     (context,))
        res = cursor.fetchall()

        if not res:
            raise LookupError("Unable to find context entry (name: %s)" % (context,))

        self.name = res[0]['context.name']
        self.displayname = res[0]['context.displayname']
        self.include = [self.name]

        for row in res:
            if row['contextinclude.include']:
                self.include.append(row['contextinclude.include'])


CALLERID_MATCHER = re.compile('^(?:"(.+)"|([a-zA-Z0-9\-\.\!%\*_\+`\'\~]+)) ?(?:<(\+?[0-9\*#]+)>)?$').match
CALLERIDNUM_MATCHER = re.compile('^\+?[0-9\*#]+$').match


class CallerID(object):
    @staticmethod
    def parse(callerid):
        logger.debug('caller_id parse: parsing "%s"', callerid)
        m = CALLERID_MATCHER(callerid)

        if not m:
            logger.debug('caller_id parse: could not match callerid, giving up')
            return

        calleridname = m.group(1)
        calleridnum = m.group(3)
        logger.debug('caller_id parse: calleridname: "%s", calleridnum: "%s"', calleridname, calleridnum)

        if calleridname is None:
            calleridname = m.group(2)
            logger.debug('caller_id parse: using fallback calleridname: calleridname: "%s", calleridnum: "%s"', calleridname, calleridnum)

            if calleridnum is None and CALLERIDNUM_MATCHER(calleridname):
                calleridnum = m.group(2)
                logger.debug('caller_id parse: using fallback calleridnum: calleridname: "%s", calleridnum: "%s"', calleridname, calleridnum)

        return (calleridname, calleridnum)

    @staticmethod
    def set(agi, callerid):
        logger.debug('caller_id set: parsing "%s"', callerid)
        cid_parsed = CallerID.parse(callerid)

        if not cid_parsed:
            logger.debug('caller_id set: parsing result: "%s", giving up', cid_parsed)
            return

        calleridname, calleridnum = cid_parsed
        logger.debug('caller_id set: calleridname: "%s", calleridnum: "%s"', calleridname, calleridnum)

        if calleridname is None and calleridnum is not None:
            calleridname = calleridnum
            logger.debug('caller_id set: using calleridnum as calleridname: calleridname: "%s", calleridnum: "%s"', calleridname, calleridnum)

        if calleridname is not None and calleridnum is None:
            logger.debug('caller_id set: applying calleridname only: calleridname: "%s"', calleridname)
            agi.set_variable('CALLERID(name)', calleridname)
        else:
            logger.debug('caller_id set: applying callerid name and num: calleridname: "%s", calleridnum: "%s"', calleridname, calleridnum)
            agi.set_variable('CALLERID(all)', '"%s" <%s>' % (calleridname, calleridnum))

        return True

    def __init__(self, agi, cursor, xtype, typeval):
        self.agi = agi
        self.cursor = cursor
        self.type = xtype
        self.typeval = typeval

        cursor.query("SELECT ${columns} FROM callerid "
                     "WHERE type = %s "
                     "AND typeval = %s "
                     "AND mode IS NOT NULL",
                     ('mode', 'callerdisplay'),
                     (xtype, typeval))
        res = cursor.fetchone()

        self.mode = None
        self.calleridname = None
        self.calleridnum = None

        if res:
            cid_parsed = self.parse(res['callerdisplay'])

            if cid_parsed:
                self.mode = res['mode']
                self.calleridname, self.calleridnum = cid_parsed
                self.calleridname = self.calleridname.encode('UTF-8')

    def rewrite(self, force_rewrite):
        """
        Set/Modify the caller ID if needed and allowed and create
        the XIVO_CID_REWRITTEN channel variable in some cases.

        @force_rewrite:
            True <=> CID modification is always allowed in this case.
                XIVO_CID_REWRITTEN is neither taken into account nor
                written.
            False <=> CID modification is only allowed if the channel
                variable XIVO_CID_REWRITTEN is not set prior to the
                call to this method.  If the CID modification really
                took place, XIVO_CID_REWRITTEN is created.
        """
        if not self.mode:
            return

        cidrewritten = self.agi.get_variable('XIVO_CID_REWRITTEN')

        if force_rewrite or not cidrewritten:

            calleridname = self.agi.get_variable('CALLERID(name)')
            calleridnum = self.agi.get_variable('CALLERID(num)')

            if self.calleridnum is not None:
                calleridnum = self.calleridnum
            elif calleridnum in (None, ''):
                calleridnum = 'unknown'

            if calleridname in (None, '', '""'):
                calleridname = calleridnum
            elif calleridname[0] == '"' and calleridname[-1] == '"':
                calleridname = calleridname[1:-1]

            if self.mode in ('prepend', 'append') \
                    and self.calleridname == calleridname \
                    and calleridnum == calleridname:
                name = calleridname
            elif self.mode == 'prepend':
                name = "%s - %s" % (self.calleridname, calleridname)
            elif self.mode == 'overwrite':
                name = self.calleridname
            elif self.mode == 'append':
                name = "%s - %s" % (calleridname, self.calleridname)
            else:
                raise RuntimeError("Unknown callerid mode: %r" % self.mode)

            self.agi.set_variable('CALLERID(name-pres)', 'allowed')
            self.agi.set_variable('CALLERID(num-pres)', 'allowed')
            self.agi.set_variable('CALLERID(all)', '"%s" <%s>' % (name, calleridnum))

            if not force_rewrite:
                self.agi.set_variable('XIVO_CID_REWRITTEN', 1)


class ChanSIP(object):

    @staticmethod
    def get_intf_and_suffix(cursor, xid):
        cursor.query(
            "SELECT ${columns} FROM endpoint_sip WHERE uuid = %s",
            ('name',),
            (xid,),
        )
        res = cursor.fetchone()

        if not res:
            raise LookupError("Unable to find usersip entry (id: {})".format(xid))

        return 'PJSIP/{}'.format(res['name']), None


class ChanIAX2(object):

    @staticmethod
    def get_intf_and_suffix(cursor, xid):

        cursor.query("SELECT ${columns} FROM useriax "
                     "WHERE id = %s "
                     "AND commented = 0",
                     ('name',),
                     (xid,))
        res = cursor.fetchone()

        if not res:
            raise LookupError("Unable to find useriax entry (id: {})".format(xid))

        return ("IAX2/%s" % res['name'], None)


class ChanCustom(object):

    @staticmethod
    def get_intf_and_suffix(cursor, xid):

        cursor.query("SELECT ${columns} FROM usercustom "
                     "WHERE id = %s "
                     "AND commented = 0",
                     ('interface', 'intfsuffix'),
                     (xid,))
        res = cursor.fetchone()

        if not res:
            raise LookupError("Unable to find usercustom entry (id: {})".format(xid))

        # In case the suffix is the integer 0, bool(intfsuffix)
        # returns False though there is a suffix. Casting it to
        # a string prevents such an error.

        return (res['interface'], str(res['intfsuffix']))
