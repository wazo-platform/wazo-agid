# Copyright 2017-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import requests


def build_sip_interface(agi, user_uuid, aor_name):
    if _is_webrtc(agi, 'PJSIP', aor_name):
        if not _is_mobile_reachable(agi, aor_name):
            # Checking for mobile connections last as this operation does HTTP requests
            if _has_mobile_connection(agi, user_uuid):
                agi.set_variable('WAZO_WAIT_FOR_MOBILE', 1)
                return f'Local/{aor_name}@wazo_wait_for_registration'

    default_interface = f'PJSIP/{aor_name}'
    registered_interfaces = agi.get_variable(f'PJSIP_DIAL_CONTACTS({aor_name})')
    return registered_interfaces or default_interface


def _has_mobile_connection(agi, user_uuid):
    mobile = False
    auth_client = agi.config['auth']['client']

    try:
        response = auth_client.token.list(user_uuid, mobile=True)
    except requests.HTTPError as e:
        agi.verbose(f'failed to fetch user refresh tokens {e}')
    else:
        mobile = response['filtered'] > 0

    if not mobile:
        try:
            response = auth_client.users.get_sessions(user_uuid)
        except requests.HTTPError as e:
            agi.verbose(f'failed to fetch user sessions {e}')
        else:
            for session in response['items']:
                if session['mobile']:
                    mobile = True
                    break

    if mobile:
        agi.set_variable('WAZO_MOBILE_CONNECTION', True)
        return True

    return False


def _is_mobile_reachable(agi, aor_name):
    raw_contacts = agi.get_variable(f'PJSIP_AOR({aor_name},contact)')
    if not raw_contacts:
        return False

    for contact in raw_contacts.split(','):
        mobility = agi.get_variable(f'PJSIP_CONTACT({contact},mobility)')
        if mobility != 'mobile':
            continue
        status = agi.get_variable(f'PJSIP_CONTACT({contact},status)')
        if status == 'Reachable':
            return True

    return False


def _is_webrtc(agi, protocol, name):
    if protocol != 'PJSIP':
        return False

    return agi.get_variable(f'PJSIP_ENDPOINT({name},webrtc)') == 'yes'
