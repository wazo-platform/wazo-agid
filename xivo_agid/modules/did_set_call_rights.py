# -*- coding: utf-8 -*-

# Copyright (C) 2006-2014 Avencall
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

from xivo_agid import agid
from xivo_agid import call_rights


def _did_set_call_rights(agi, cursor, args):
    srcnum = agi.get_variable('XIVO_SRCNUM')
    incall_id = agi.get_variable('XIVO_INCALL_ID')

    cursor.query("SELECT ${columns} FROM rightcallexten",
                 ('rightcallid', 'exten'))
    res = cursor.fetchall()

    if not res:
        call_rights.allow(agi)

    rightcallidset = set((row['rightcallid'] for row in res if call_rights.extension_matches(srcnum, row['exten'])))

    if not rightcallidset:
        call_rights.allow(agi)

    rightcallids = '(' + ','.join((str(el) for el in rightcallidset)) + ')'
    cursor.query("SELECT ${columns} FROM rightcall "
                 "INNER JOIN rightcallmember "
                 "ON rightcall.id = rightcallmember.rightcallid "
                 "INNER JOIN incall "
                 "ON CAST(rightcallmember.typeval AS integer) = incall.id "
                 "WHERE rightcall.id IN " + rightcallids + " "
                 "AND rightcallmember.type = 'incall' "
                 "AND incall.id = %s "
                 "AND rightcall.commented = 0",
                 (call_rights.RIGHTCALL_AUTHORIZATION_COLNAME, call_rights.RIGHTCALL_PASSWD_COLNAME),
                 [incall_id])
    res = cursor.fetchall()
    call_rights.apply_rules(agi, res)
    call_rights.allow(agi)


def did_set_call_rights(agi, cursor, args):
    try:
        _did_set_call_rights(agi, cursor, args)
    except call_rights.RuleAppliedException:
        return


agid.register(did_set_call_rights)
