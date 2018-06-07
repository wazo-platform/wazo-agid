# -*- coding: utf-8 -*-
# Copyright (C) 2006-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

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
