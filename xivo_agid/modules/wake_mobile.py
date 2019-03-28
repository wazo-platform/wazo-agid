# -*- coding: utf-8 -*-
# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import time
from xivo_agid import agid

def _is_registered(agi, aor_name):
    aor = agi.get_variable('PJSIP_AOR({},contact)'.format(aor_name))
    return True if aor else False


def _wait_for_registration(agi, aor_name, timeout):
    for _ in xrange(timeout * 4):
        if _is_registered(agi, aor_name):
            return

        time.sleep(0.25)


def _is_webrtc(agi, protocol, name):
    if protocol != 'PJSIP':
        return False

    return agi.get_variable('PJSIP_ENDPOINT({},webrtc)'.format(name)) == 'yes'


def wake_mobile(agi, cursor, args):
    interfaces = agi.get_variable('XIVO_INTERFACE').split('&')
    user_uuid = agi.get_variable('WAZO_DST_UUID')
    timeout = int(agi.get_variable('XIVO_RINGSECONDS'))

    for interface in interfaces:
        protocol, end = interface.split('/', 1)
        name = end.split('/', 1)[0]
        if not _is_webrtc(agi, protocol, name):
            continue

        agi.appexec('UserEvent', 'Pushmobile,WAZO_DST_UUID: {}'.format(user_uuid))
        _wait_for_registration(agi, name, timeout)


agid.register(wake_mobile)
