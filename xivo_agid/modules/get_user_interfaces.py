# -*- coding: utf-8 -*-
# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from xivo_agid import (
    agid,
    objects,
)


def get_user_interfaces(agi, cursor, args):
    user_uuid = args[0]
    user_line = objects.UserLine(agi, user_uuid)
    interfaces = user_line.interfaces
    agi.set_variable('WAZO_USER_INTERFACES', '{interfaces}'.format(interfaces='&'.join(interfaces)))


agid.register(get_user_interfaces)
