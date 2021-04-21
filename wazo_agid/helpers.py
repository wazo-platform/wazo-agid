# -*- coding: utf-8 -*-
# Copyright 2017-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


def is_webrtc(agi, protocol, name):
    if protocol != 'PJSIP':
        return False

    return agi.get_variable('PJSIP_ENDPOINT({},webrtc)'.format(name)) == 'yes'


def is_registered_and_mobile(agi, aor_name):
    raw_contacts = agi.get_variable('PJSIP_AOR({},contact)'.format(aor_name))
    if not raw_contacts:
        return False

    for contact in raw_contacts.split(','):
        mobility = agi.get_variable('PJSIP_CONTACT({},mobility)'.format(contact))
        if mobility == 'mobile':
            return True

    return False
