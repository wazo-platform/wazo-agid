# -*- coding: utf-8 -*-
# Copyright 2017-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import requests


def build_sip_interface(agi, user_uuid, aor_name):
    if _is_webrtc(agi, 'PJSIP', aor_name):
        if not _is_registered_and_mobile(agi, aor_name):
            # Checking for mobile connections last as this operation does HTTP requests
            if _has_mobile_connection(agi, user_uuid):
                agi.set_variable('WAZO_WAIT_FOR_MOBILE', 1)
                return 'Local/{}@wazo_wait_for_registration'.format(aor_name)

    default_interface = 'PJSIP/{}'.format(aor_name)
    registered_interfaces = agi.get_variable('PJSIP_DIAL_CONTACTS({})'.format(aor_name))
    return registered_interfaces or default_interface


def _has_mobile_connection(agi, user_uuid):
    mobile = False
    auth_client = agi.config['auth']['client']

    try:
        response = auth_client.token.list(user_uuid, mobile=True)
    except requests.HTTPError as e:
        agi.verbose('failed to fetch user refresh tokens {}'.format(e))
    else:
        mobile = response['filtered'] > 0

    if not mobile:
        try:
            response = auth_client.users.get_sessions(user_uuid)
        except requests.HTTPError as e:
            agi.verbose('failed to fetch user sessions {}'.format(e))
        else:
            for session in response['items']:
                if session['mobile']:
                    mobile = True
                    break

    if mobile:
        agi.set_variable('WAZO_MOBILE_CONNECTION', True)
        return True

    return False


def _is_registered_and_mobile(agi, aor_name):
    raw_contacts = agi.get_variable('PJSIP_AOR({},contact)'.format(aor_name))
    if not raw_contacts:
        return False

    for contact in raw_contacts.split(','):
        mobility = agi.get_variable('PJSIP_CONTACT({},mobility)'.format(contact))
        if mobility == 'mobile':
            return True

    return False


def _is_webrtc(agi, protocol, name):
    if protocol != 'PJSIP':
        return False

    return agi.get_variable('PJSIP_ENDPOINT({},webrtc)'.format(name)) == 'yes'
