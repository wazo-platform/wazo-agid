# -*- coding: utf-8 -*-

__license__ = """
    Copyright (C) 2006-2010  Avencall

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

from xivo_agid import agid
from xivo_agid import objects

def incoming_group_set_features(agi, cursor, args):
    groupid = agi.get_variable('XIVO_DSTID')
    referer = agi.get_variable('XIVO_FWD_REFERER')

    try:
        group = objects.Group(agi, cursor, xid=int(groupid))
    except (ValueError, LookupError), e:
        agi.dp_break(str(e))

    options = ""
    needanswer = "1"

    if group.transfer_user:
        options += "t"

    if group.transfer_call:
        options += "T"

    if group.write_caller:
        options += "w"

    if group.write_calling:
        options += "W"

    if not group.musicclass:
        options += "r"
        needanswer = "0"

    agi.set_variable('XIVO_REAL_NUMBER', group.number)
    agi.set_variable('XIVO_REAL_CONTEXT', group.context)
    agi.set_variable('XIVO_GROUPNAME', group.name)
    agi.set_variable('XIVO_GROUPOPTIONS', options)
    agi.set_variable('XIVO_GROUPNEEDANSWER', needanswer)

    if group.preprocess_subroutine:
        preprocess_subroutine = group.preprocess_subroutine
    else:
        preprocess_subroutine = ""

    if group.timeout:
        timeout = group.timeout
    else:
        timeout = ""

    agi.set_variable('XIVO_GROUPPREPROCESS_SUBROUTINE', preprocess_subroutine)
    agi.set_variable('XIVO_GROUPTIMEOUT', timeout)

    group.set_dial_actions()

    if referer == ("group:%s" % group.id) or referer.startswith("voicemenu:"):
        group.rewrite_cid()

    # schedule
    path = agi.get_variable('XIVO_PATH')
    if path is None or len(path) == 0:
        agi.set_variable('XIVO_PATH'   , 'group')
        agi.set_variable('XIVO_PATH_ID', group.id)

agid.register(incoming_group_set_features)
