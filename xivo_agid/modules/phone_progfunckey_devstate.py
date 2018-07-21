# -*- coding: utf-8 -*-
# Copyright 2009-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from xivo.xivo_helpers import fkey_extension

from xivo_agid import agid, objects


def phone_progfunckey_devstate(agi, cursor, args):
    userid = agi.get_variable('XIVO_USERID')
    xlen = len(args)

    if xlen < 2:
        agi.dp_break("Invalid number of arguments (args: %r)" % args)

    devstate = args[1]

    if devstate not in ('BUSY',
                        'INUSE',
                        'INVALID',
                        'NOT_INUSE',
                        'ONHOLD',
                        'RINGING',
                        'RINGINUSE',
                        'UNAVAILABLE',
                        'UNKNOWN'):
        agi.dp_break("Invalid device state: %r" % devstate)

    try:
        user = objects.User(agi, cursor, int(userid))
    except (ValueError, LookupError) as e:
        agi.dp_break(str(e))

    feature = args[0]

    if xlen > 2:
        dest = args[2]
    else:
        dest = ""

    try:
        extenfeatures = objects.ExtenFeatures(agi, cursor)
        ppfkexten = extenfeatures.get_exten_by_name('phoneprogfunckey')
    except LookupError as e:
        agi.verbose(str(e))
        return

    if feature not in extenfeatures.featureslist:
        agi.verbose("Invalid feature: %r" % feature)
        return

    forwards = dict(extenfeatures.FEATURES['forwards'])
    services_api = ['incallfilter', 'enablednd']
    if feature in forwards or feature in services_api:
        return

    try:
        featureexten = extenfeatures.get_exten_by_name(feature)
    except LookupError as e:
        agi.verbose(str(e))
        return

    xset = set()
    xset.add(fkey_extension(ppfkexten,
                            (user.id,
                             featureexten,
                             dest)))

    for x in xset:
        agi.set_variable("DEVICE_STATE(Custom:%s)" % x, devstate)


agid.register(phone_progfunckey_devstate)
