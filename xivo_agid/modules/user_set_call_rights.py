# -*- coding: utf-8 -*-
# Copyright (C) 2006-2016 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from xivo_agid import agid
from xivo_agid import objects
from xivo_agid import call_rights

logger = logging.getLogger(__name__)


def _user_set_call_rights(agi, cursor, args):
    userid = agi.get_variable('XIVO_USERID')
    dstnum = agi.get_variable('XIVO_DSTNUM')
    outcallid = agi.get_variable('XIVO_OUTCALLID')

    cursor.query("SELECT ${columns} FROM rightcallexten",
                 ('rightcallid', 'exten'))
    res = cursor.fetchall()

    if not res:
        call_rights.allow(agi)

    rightcallidset = set((row['rightcallid'] for row in res if call_rights.extension_matches(dstnum, row['exten'])))

    if not rightcallidset:
        call_rights.allow(agi)

    rightcallids = '(' + ','.join((str(el) for el in rightcallidset)) + ')'

    try:
        user = objects.User(agi, cursor, int(userid))
    except (ValueError, LookupError):
        if not outcallid:
            call_rights.allow(agi)
    else:
        cursor.query("SELECT ${columns} FROM rightcall "
                     "INNER JOIN rightcallmember "
                     "ON rightcall.id = rightcallmember.rightcallid "
                     "WHERE rightcall.id IN " + rightcallids + " "
                     "AND rightcallmember.type = 'user' "
                     "AND rightcallmember.typeval = '%s' "
                     "AND rightcall.commented = 0",
                     (call_rights.RIGHTCALL_AUTHORIZATION_COLNAME,
                      call_rights.RIGHTCALL_PASSWD_COLNAME),
                     (user.id,))
        res = cursor.fetchall()

        if user.rightcallcode:
            for i, value in enumerate(res):
                if value[1]:
                    res[i][1] = user.rightcallcode

        call_rights.apply_rules(agi, res)

        cursor.query("SELECT ${columns} FROM groupfeatures "
                     "INNER JOIN queuemember "
                     "ON groupfeatures.name = queuemember.queue_name "
                     "INNER JOIN queue "
                     "ON queue.name = queuemember.queue_name "
                     "WHERE groupfeatures.deleted = 0 "
                     "AND queuemember.userid = %s "
                     "AND queuemember.usertype = 'user' "
                     "AND queuemember.category = 'group' "
                     "AND queuemember.commented = 0 "
                     "AND queue.category = 'group' "
                     "AND queue.commented = 0",
                     ('groupfeatures.id',),
                     (user.id,))
        res = cursor.fetchall()

        if res:
            groupids = [row['groupfeatures.id'] for row in res]
            cursor.query("SELECT ${columns} FROM rightcall "
                         "INNER JOIN rightcallmember "
                         "ON rightcall.id = rightcallmember.rightcallid "
                         "WHERE rightcall.id IN " + rightcallids + " "
                         "AND rightcallmember.type = 'group' "
                         "AND rightcallmember.typeval IN (" + ", ".join(["'%s'"] * len(res)) + ") "
                         "AND rightcall.commented = 0",
                         (call_rights.RIGHTCALL_AUTHORIZATION_COLNAME,
                          call_rights.RIGHTCALL_PASSWD_COLNAME),
                         groupids)
            res = cursor.fetchall()
            call_rights.apply_rules(agi, res)

    if outcallid:
        cursor.query("SELECT ${columns} FROM rightcall "
                     "INNER JOIN rightcallmember "
                     "ON rightcall.id = rightcallmember.rightcallid "
                     "INNER JOIN outcall "
                     "ON CAST(rightcallmember.typeval AS integer) = outcall.id "
                     "WHERE rightcall.id IN " + rightcallids + " "
                     "AND rightcallmember.type = 'outcall' "
                     "AND outcall.id = %s "
                     "AND rightcall.commented = 0",
                     (call_rights.RIGHTCALL_AUTHORIZATION_COLNAME,
                      call_rights.RIGHTCALL_PASSWD_COLNAME),
                     (outcallid,))
        res = cursor.fetchall()
        call_rights.apply_rules(agi, res)

    call_rights.allow(agi)


def user_set_call_rights(agi, cursor, args):
    try:
        _user_set_call_rights(agi, cursor, args)
    except call_rights.RuleAppliedException:
        return


agid.register(user_set_call_rights)
