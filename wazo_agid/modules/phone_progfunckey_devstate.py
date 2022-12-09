# Copyright 2009-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from xivo.xivo_helpers import fkey_extension

from wazo_agid import agid, objects


def phone_progfunckey_devstate(agi, cursor, args):
    userid = agi.get_variable('XIVO_USERID')
    arg_count = len(args)

    if arg_count < 2:
        agi.dp_break(f"Invalid number of arguments (args: {args!r})")

    devstate = args[1]

    if devstate not in (
        'BUSY',
        'INUSE',
        'INVALID',
        'NOT_INUSE',
        'ONHOLD',
        'RINGING',
        'RINGINUSE',
        'UNAVAILABLE',
        'UNKNOWN',
    ):
        agi.dp_break(f"Invalid device state: {devstate!r}")

    try:
        user = objects.User(agi, cursor, int(userid))
    except (ValueError, LookupError) as e:
        agi.dp_break(str(e))

    feature = args[0]

    if arg_count > 2:
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
        agi.verbose(f"Invalid feature: {feature!r}")
        return

    forwards = extenfeatures.FEATURES['forwards']
    services_api = ['incallfilter', 'enablednd']
    if feature in forwards or feature in services_api:
        return

    try:
        featureexten = extenfeatures.get_exten_by_name(feature)
    except LookupError as e:
        agi.verbose(str(e))
        return

    exten = fkey_extension(ppfkexten, (user.id, featureexten, dest))
    agi.set_variable(f"DEVICE_STATE(Custom:{exten})", devstate)


agid.register(phone_progfunckey_devstate)
