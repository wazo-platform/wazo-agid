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
from xivo_agid import objects


def incoming_did_set_features(agi, cursor, args):
    incall_id = agi.get_variable('XIVO_INCALL_ID')

    did = objects.DID(agi, cursor, xid=incall_id)

    if did.preprocess_subroutine:
        preprocess_subroutine = did.preprocess_subroutine
    else:
        preprocess_subroutine = ""

    agi.set_variable('XIVO_DIDPREPROCESS_SUBROUTINE', preprocess_subroutine)
    agi.set_variable('XIVO_EXTENPATTERN', did.exten)
    agi.set_variable('XIVO_PATH', 'incall')
    agi.set_variable('XIVO_PATH_ID', did.id)
    agi.set_variable('XIVO_REAL_CONTEXT', did.context)
    agi.set_variable('XIVO_REAL_NUMBER', did.exten)

    did.set_dial_actions()
    did.rewrite_cid()


agid.register(incoming_did_set_features)
