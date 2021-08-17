# -*- coding: utf-8 -*-
# Copyright 2018-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from wazo_agid import agid


class UnknownUser(Exception):
    pass


class _UserLine:

    def __init__(self, agi, user_uuid):
        self._agi = agi
        self.interfaces = []
        hint = agi.get_variable('HINT({}@usersharedlines)'.format(user_uuid))
        if not hint:
            raise UnknownUser()

        for endpoint in hint.split('&'):
            if '/' not in endpoint:
                continue

            for interface in self._find_matching_interfaces(endpoint):
                self.interfaces.append(interface)

    def _find_matching_interfaces(self, endpoint):
        protocol, name = endpoint.split('/', 1)
        if protocol == 'pjsip':
            contacts = self._agi.get_variable('PJSIP_DIAL_CONTACTS({name})'.format(name=name))
            if not contacts:
                return

            for contact in contacts.split('&'):
                yield contact
        else:
            yield endpoint


def get_user_interfaces(agi, cursor, args):
    user_uuid = args[0]
    user_line = _UserLine(agi, user_uuid)
    interfaces = user_line.interfaces
    agi.set_variable('WAZO_USER_INTERFACES', '{interfaces}'.format(interfaces='&'.join(interfaces)))


agid.register(get_user_interfaces)
