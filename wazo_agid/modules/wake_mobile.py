# -*- coding: utf-8 -*-
# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import time
from wazo_agid import agid
from wazo_agid.helpers import (
    is_registered_and_mobile,
    is_webrtc,
)


class TimeoutReachedException(Exception):
    pass


def _is_registered(agi, aor_name):
    aor = agi.get_variable('PJSIP_AOR({},contact)'.format(aor_name))
    return True if aor else False


def _wait_for_registration(agi, aor_name, timeout):
    for _ in xrange(timeout * 4):
        if _is_registered(agi, aor_name):
            return

        time.sleep(0.25)

    raise TimeoutReachedException()


def wake_mobile(agi, cursor, args):
    has_mobile_session = agi.get_variable('WAZO_MOBILE_SESSION') or False
    if not has_mobile_session:
        return

    interfaces = agi.get_variable('XIVO_INTERFACE').split('&')
    should_wake_mobile = False

    for interface in interfaces:
        protocol, end = interface.split('/', 1)
        name = end.split('/', 1)[0]
        if not is_webrtc(agi, protocol, name):
            continue

        if is_registered_and_mobile(agi, name):
            return

        should_wake_mobile = True
        break

    if should_wake_mobile:
        user_uuid = agi.get_variable('WAZO_DST_UUID')
        agi.appexec('UserEvent', 'Pushmobile,WAZO_DST_UUID: {}'.format(user_uuid))


def wait_for_registration(agi, cursor, args):
    aor = args[0]
    timeout = int(agi.get_variable('PJSIP_ENDPOINT({},@wake_mobile_timeout)'.format(aor)) or 30)

    try:
        _wait_for_registration(agi, aor, timeout)
    except TimeoutReachedException:
        agi.verbose('Timeout reached on {} registration {}'.format(aor, timeout))
    else:
        contacts = agi.get_variable('PJSIP_DIAL_CONTACTS({aor})'.format(aor=aor))
        agi.set_variable('WAZO_DIAL_CONTACTS', contacts)


agid.register(wake_mobile)
agid.register(wait_for_registration)
