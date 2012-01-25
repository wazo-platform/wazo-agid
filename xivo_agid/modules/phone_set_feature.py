# -*- coding: utf-8 -*-

__license__ = """
    Copyright (C) 2006-2012  Avencall

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from xivo_agid import agid
from xivo_agid import objects


def phone_set_feature(agi, cursor, args):
    try:
        feature_name = args[0]
    except IndexError:
        agi.dp_break('Missing feature name argument')

    function_name = '_phone_set_%s' % feature_name
    try:
        function = globals()[function_name]
    except KeyError:
        agi.dp_break('Unknown feature name %r' % feature_name)

    try:
        function(agi, cursor, args)
    except LookupError, e:
        agi.dp_break(str(e))


def _phone_set_callrecord(agi, cursor, args):
    calling_user = _get_calling_user(agi, cursor)
    calling_user.toggle_feature('callrecord')

    agi.set_variable('XIVO_CALLRECORDENABLED', calling_user.callrecord)
    agi.set_variable('XIVO_USERID_OWNER', calling_user.id)


def _get_calling_user(agi, cursor):
    return objects.User(agi, cursor, _get_id_of_calling_user(agi))


def _get_id_of_calling_user(agi):
    return int(agi.get_variable('XIVO_USERID'))


def _phone_set_dnd(agi, cursor, args):
    calling_user = _get_calling_user(agi, cursor)
    calling_user.toggle_feature('enablednd')

    agi.set_variable('XIVO_DNDENABLED', calling_user.enablednd)
    agi.set_variable('XIVO_USERID_OWNER', calling_user.id)


def _phone_set_incallfilter(agi, cursor, args):
    calling_user = _get_calling_user(agi, cursor)
    calling_user.toggle_feature('incallfilter')

    agi.set_variable('XIVO_INCALLFILTERENABLED', calling_user.incallfilter)
    agi.set_variable('XIVO_USERID_OWNER', calling_user.id)


def _phone_set_vm(agi, cursor, args):
    exten = args[1]
    if exten:
        user = _get_user_from_exten(agi, cursor, exten)
    else:
        user = _get_calling_user(agi, cursor)

    vmbox = objects.VMBox(agi, cursor, user.voicemailid, commentcond=False)
    if vmbox.password and user.id != _get_id_of_calling_user(agi):
        agi.appexec('Authenticate', vmbox.password)

    user.toggle_feature('enablevoicemail')

    agi.set_variable('XIVO_VMENABLED', user.enablevoicemail)
    agi.set_variable('XIVO_USERID_OWNER', user.id)


def _get_user_from_exten(agi, cursor, exten):
    context = _get_context_of_calling_user(agi, cursor)

    return objects.User(agi, cursor, exten=exten, context=context)


def _get_context_of_calling_user(agi, cursor):
    master_line = objects.MasterLineUser(agi, cursor, _get_id_of_calling_user(agi))
    return master_line.line['context']


def _phone_set_bsfilter(agi, cursor, args):
    exten = args[1]
    calling_user = _get_calling_user(agi, cursor)

    master_line = objects.MasterLineUser(agi, cursor, calling_user.id)

    ml_number = master_line.line['number']

    try:
        num1, num2 = exten.split('*')
        if ml_number not in (num1, num2):
            raise ValueError('Invalid number')
    except ValueError:
        agi.dp_break('Invalid number')

    bsf = None
    secretary = None

    # Both the boss and secretary numbers are passed, so select the one
    if ml_number == num1:
        number = num2
    else:
        number = num1

    if calling_user.bsfilter == 'secretary':
        try:
            bsf = objects.BossSecretaryFilter(agi, cursor, master_line.line)
            secretary_number = ml_number
        except LookupError:
            pass
    elif calling_user.bsfilter == 'boss':
        bsf = calling_user.filter
        secretary_number = number

    if bsf:
        bsf.set_dial_actions()
        secretary = bsf.get_secretary_by_number(secretary_number)

    if not secretary:
        agi.dp_break("Unable to find boss-secretary filter")

    agi.verbose("Filter exists! (Caller: %r, secretary number: %r)" % (calling_user.bsfilter,
                                                                       secretary_number))
    cursor.query("SELECT ${columns} FROM callfiltermember "
                 "WHERE callfilterid = %s "
                 "AND type = %s "
                 "AND " + cursor.cast('typeval', 'int') + " = %s "
                 "AND bstype = %s",
                 ('active',),
                 (bsf.id, "user", secretary.id, "secretary"))
    res = cursor.fetchone()

    if not res:
        agi.dp_break("Unable to find secretary (id = %d)" % secretary.id)

    new_state = int(not res['active'])
    cursor.query("UPDATE callfiltermember "
                 "SET active = %s "
                 "WHERE callfilterid = %s "
                 "AND type = %s "
                 "AND " + cursor.cast('typeval', 'int') + " = %s "
                 "AND bstype = %s",
                 parameters=(new_state, bsf.id, "user", secretary.id, "secretary"))

    if cursor.rowcount != 1:
        agi.dp_break('Unable to perform the requested update')

    agi.set_variable('XIVO_BSFILTERENABLED', new_state)


def _phone_set_unc(agi, cursor, args):
    _do_phone_set_forward(agi, cursor, args, 'unc')


def _phone_set_rna(agi, cursor, args):
    _do_phone_set_forward(agi, cursor, args, 'rna')


def _phone_set_busy(agi, cursor, args):
    _do_phone_set_forward(agi, cursor, args, 'busy')


def _do_phone_set_forward(agi, cursor, args, forward_name):
    enable = int(args[1])
    destination = args[2]

    calling_user = _get_calling_user(agi, cursor)
    calling_user.set_feature(forward_name, enable, destination)

    agi.set_variable('XIVO_%sENABLED' % forward_name.upper(),
                     getattr(calling_user, 'enable%s' % forward_name))
    agi.set_variable('XIVO_USERID_OWNER', calling_user.id)


agid.register(phone_set_feature)
