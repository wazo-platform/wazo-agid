# Copyright 2006-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from wazo_agid import agid

logger = logging.getLogger(__name__)


def fwdundoall(agi, cursor, args):
    user_id = _get_id_of_calling_user(agi)
    _user_disable_all_forwards(agi, user_id)


def _get_id_of_calling_user(agi):
    return int(agi.get_variable('XIVO_USERID'))


def _user_disable_all_forwards(agi, user_id):
    try:
        confd_client = agi.config['confd']['client']
        disabled = {'enabled': False}
        body = {'busy': disabled, 'noanswer': disabled, 'unconditional': disabled}
        confd_client.users(user_id).update_forwards(body)
    except Exception as e:
        logger.error('Error during disabling all forwards: %s', e)


agid.register(fwdundoall)
