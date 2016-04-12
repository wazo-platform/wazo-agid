# -*- coding: utf-8 -*-

# Copyright (C) 2006-2016 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import logging

from xivo_agid import agid

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
        body = {'busy': disabled,
                'noanswer': disabled,
                'unconditional': disabled}
        confd_client.users(user_id).update_forwards(body)
    except Exception, e:
        logger.error('Error during disabling all forwards: %s', e)

agid.register(fwdundoall)
