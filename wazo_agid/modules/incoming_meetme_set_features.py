# -*- coding: utf-8 -*-
# Copyright (C) 2006-2014 Avencall
# SPDX-License-Identifier: GPL-3.0-or-later

import time

from xivo_agid import agid
from xivo_agid import objects


MEETME_RECORDINGDIR = '/var/lib/asterisk/sounds/meetme/'


def conf_exceed_max_number(agi, confno, maxuser):
    if not maxuser or int(maxuser) < 1:
        return False

    agi.appexec('MeetMeCount', "%s,MEETMECOUNT" % confno)
    meetmecount = agi.get_variable('MEETMECOUNT')

    if not meetmecount.isdigit():
        return None

    return (int(meetmecount) >= int(maxuser))


def conf_is_open(starttime, durationm):
    if not starttime:
        return True
    elif starttime > time.time():
        return False
    elif durationm:
        return ((starttime + (int(durationm) * 60)) > time.time())
    else:
        return True


def incoming_meetme_set_features(agi, cursor, args):
    xid = agi.get_variable('XIVO_DSTID')

    try:
        meetme = objects.MeetMe(agi,
                                cursor,
                                int(xid))
    except (ValueError, LookupError), e:
        agi.dp_break(str(e))

    if not conf_is_open(meetme.starttime, meetme.durationm):
        # TODO: Change sound by conf-closed
        agi.appexec('Playback', "conf-locked&vm-goodbye")
        agi.dp_break("Unable to join the conference room, it's not open "
                     "(start date: %r, current date: %s, duration minutes: %r, id: %s, name: %s, confno: %s)"
                     % (meetme.startdate,
                        time.strftime('%Y-%m-%d %H:%M:%S'),
                        meetme.durationm,
                        meetme.id,
                        meetme.name,
                        meetme.confno))

    options = ''.join(meetme.get_global_options())

    pin = meetme.pin
    options += ''.join(meetme.get_user_options())

    if conf_exceed_max_number(agi, meetme.confno, meetme.maxusers):
        # TODO: Change sound by conf-maxuserexceeded
        agi.appexec('Playback', "conf-locked&vm-goodbye")
        agi.dp_break("Unable to join the conference room, max number of users exceeded "
                     "(max number: %s, id: %s, name: %s, confno: %s)"
                     % (meetme.maxusers, meetme.id, meetme.name, meetme.confno))

    if meetme.OPTIONS_COMMON['musiconhold'] in options:
        agi.set_variable('CHANNEL(musicclass)',
                         meetme.get_user_option('musiconhold'))

    if meetme.OPTIONS_COMMON['enableexitcontext'] in options:
        exitcontext = meetme.get_user_option('exitcontext')
    else:
        exitcontext = ""

    if meetme.preprocess_subroutine:
        preprocess_subroutine = meetme.preprocess_subroutine
    else:
        preprocess_subroutine = ""

    agi.set_variable('MEETME_EXIT_CONTEXT', exitcontext)
    agi.set_variable('MEETME_RECORDINGFILE', MEETME_RECORDINGDIR + "meetme-%s-%s" % (meetme.confno, int(time.time())))

    agi.set_variable('XIVO_REAL_NUMBER', meetme.confno)
    agi.set_variable('XIVO_REAL_CONTEXT', meetme.context)
    agi.set_variable('XIVO_MEETMECONFNO', meetme.confno)
    agi.set_variable('XIVO_MEETMENAME', meetme.name)
    agi.set_variable('XIVO_MEETMENUMBER', meetme.confno)
    agi.set_variable('XIVO_MEETMEPIN', pin)
    agi.set_variable('XIVO_MEETMEOPTIONS', options)
    agi.set_variable('XIVO_MEETMEPREPROCESS_SUBROUTINE', preprocess_subroutine)


agid.register(incoming_meetme_set_features)
