# Copyright 2006-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
from psycopg2.extras import DictCursor
from psycopg2.sql import SQL

from wazo_agid import agid
from wazo_agid import objects
from wazo_agid import call_rights
from wazo_agid.objects import join_column_names

logger = logging.getLogger(__name__)


def _user_set_call_rights(agi, cursor: DictCursor, args):
    userid = agi.get_variable('XIVO_USERID')
    dstnum = agi.get_variable('XIVO_DSTNUM')
    outcallid = agi.get_variable('XIVO_OUTCALLID')

    cursor.execute("SELECT rightcallid, exten FROM rightcallexten")
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
        query = SQL(
            "SELECT {columns} FROM rightcall "
            "INNER JOIN rightcallmember "
            "ON rightcall.id = rightcallmember.rightcallid "
            "WHERE rightcall.id IN " + rightcallids + " "
            "AND rightcallmember.type = 'user' "
            "AND rightcallmember.typeval = '%s' "
            "AND rightcall.commented = 0"
        )
        columns = (call_rights.RIGHTCALL_AUTHORIZATION_COLNAME, call_rights.RIGHTCALL_PASSWD_COLNAME)
        cursor.execute(query.format(columns=join_column_names(columns)), (user.id,))
        res: list[DictCursor] = cursor.fetchall()

        if user.rightcallcode:
            for i, value in enumerate(res):
                if value[1]:
                    res[i][1] = user.rightcallcode

        call_rights.apply_rules(agi, res)

        cursor.execute(
            "SELECT groupfeatures.id FROM groupfeatures "
             "INNER JOIN queuemember "
             "ON groupfeatures.name = queuemember.queue_name "
             "INNER JOIN queue "
             "ON queue.name = queuemember.queue_name "
             "WHERE queuemember.userid = %s "
             "AND queuemember.usertype = 'user' "
             "AND queuemember.category = 'group' "
             "AND queuemember.commented = 0 "
             "AND queue.category = 'group' "
             "AND queue.commented = 0",
             (user.id,)
        )
        res = cursor.fetchall()

        if res:
            groupids = [row['id'] for row in res]
            columns = (call_rights.RIGHTCALL_AUTHORIZATION_COLNAME, call_rights.RIGHTCALL_PASSWD_COLNAME),
            query = SQL(
                "SELECT {columns} FROM rightcall "
                "INNER JOIN rightcallmember "
                "ON rightcall.id = rightcallmember.rightcallid "
                "WHERE rightcall.id IN " + rightcallids + " "
                "AND rightcallmember.type = 'group' "
                "AND rightcallmember.typeval IN (" + ", ".join(["'%s'"] * len(res)) + ") "
                "AND rightcall.commented = 0"
            )
            cursor.execute(query.format(columns=join_column_names(columns)), groupids)
            res = cursor.fetchall()
            call_rights.apply_rules(agi, res)

    if outcallid:
        columns = (call_rights.RIGHTCALL_AUTHORIZATION_COLNAME, call_rights.RIGHTCALL_PASSWD_COLNAME)
        query = SQL(
            "SELECT {columns} FROM rightcall "
            "INNER JOIN rightcallmember "
            "ON rightcall.id = rightcallmember.rightcallid "
            "INNER JOIN outcall "
            "ON CAST(rightcallmember.typeval AS integer) = outcall.id "
            "WHERE rightcall.id IN " + rightcallids + " "
            "AND rightcallmember.type = 'outcall' "
            "AND outcall.id = %s "
            "AND rightcall.commented = 0",
        )
        cursor.execute(query.format(columns=join_column_names(columns)), (outcallid,))
        res = cursor.fetchall()
        call_rights.apply_rules(agi, res)

    call_rights.allow(agi)


def user_set_call_rights(agi, cursor, args):
    try:
        _user_set_call_rights(agi, cursor, args)
    except call_rights.RuleAppliedException:
        return


agid.register(user_set_call_rights)
