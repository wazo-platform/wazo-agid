# -*- coding: utf-8 -*-
# Copyright 2009-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from xivo.xivo_helpers import split_extension

from wazo_agid import agid, objects


def phone_progfunckey(agi, cursor, args):
    userid = agi.get_variable('XIVO_USERID')
    xlen = len(args)

    if xlen != 1:
        agi.dp_break("Invalid number of arguments (args: %r)" % args)

    try:
        fklist = split_extension(args[0])
    except ValueError as e:
        agi.dp_break(str(e))

    if userid != fklist[0]:
        agi.dp_break("Wrong userid. (userid: %r, excepted: %r)" % (fklist[0], userid))

    feature = ""

    try:
        extenfeatures = objects.ExtenFeatures(agi, cursor)
        feature = extenfeatures.get_name_by_exten(fklist[1])
    except LookupError as e:
        feature = ""
        agi.verbose(str(e))

    agi.set_variable('XIVO_PHONE_PROGFUNCKEY', ''.join(fklist[1:]))
    agi.set_variable('XIVO_PHONE_PROGFUNCKEY_FEATURE', feature)


agid.register(phone_progfunckey)
