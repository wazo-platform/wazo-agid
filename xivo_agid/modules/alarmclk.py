# -*- coding: UTF-8 -*-

__license__ = """
    Copyright (C) 2011  Proformatique <technique@proformatique.com>

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

import json
import logging
import urllib2
from xivo_agid import agid
from xivo_agid import objects

logger = logging.getLogger(__name__)

USERS_URL = 'http://localhost/service/ipbx/json.php/private/pbx_settings/users/'
TIMEOUT = 10


def _get_user_webi(userid):
    url = USERS_URL + '?act=view&id=%s' % userid
    f = urllib2.urlopen(url, timeout=TIMEOUT)
    try:
        return json.load(f)
    finally:
        f.close()


def _set_user_webi(userid, content):
    url = USERS_URL + '?act=edit&id=%s' % userid
    data = json.dumps(content)
    request = urllib2.Request(url, data)
    f = urllib2.urlopen(request, timeout=TIMEOUT)
    try:
        f.read()
    finally:
        f.close()


def _update_alarmclock_webi(userid, alarm_clock):
    content = _get_user_webi(userid)
    new_content = {
        'userfeatures': content['userfeatures'],
        'dialaction': {
            'noanswer': {'actiontype': 'none'},
            'busy': {'actiontype': 'none'},
            'congestion': {'actiontype': 'none'},
            'chanunavail': {'actiontype': 'none'},
        }
    }
    new_content['userfeatures']['alarmclock'] = alarm_clock
    _set_user_webi(userid, new_content)


def _get_alarmclock_db(cursor, userid):
    cursor.query("SELECT ${columns} "
                 "FROM userfeatures "
                 "WHERE id = %s",
                 ('alarmclock',),
                 (userid,))
    results = cursor.fetchall()
    if not results:
        logger.warning('Could not retrieve alarmclock for user %s: no such user',
                       userid)
        return ''
    else:
        return results[0][0]


def _update_alarmclock_db(cursor, userid, alarm_clock):
    # Only to be used when the alarm scheduler in the CTI server doesn't
    # need to be warned the alarm clock field of a user changed.
    cursor.query("UPDATE userfeatures "
                 "SET alarmclock = %s "
                 "WHERE id = %s",
                 parameters=(alarm_clock, userid))


def _set_interface_vars(agi, cursor, userid):
    try:
        lines = objects.Lines(agi, cursor, userid)
    except LookupError:
        logger.error("Can't alarm user %s because it seems this user has no lines")
        agi.set_variable('XIVO_INTERFACE', '0')
    else:
        # the current behaviour for the alarm clock is to make all the lines ring
        # at the same time whatsoever
        interface = '&'.join('%s/%s' % (l['protocol'], l['name']) for
                             l in lines.lines)
        agi.set_variable('XIVO_INTERFACE', interface)


def alarmclk_pre_execute(agi, cursor, args):
    userid = int(args[0])
    
    _update_alarmclock_db(cursor, userid, '')
    _set_interface_vars(agi, cursor, userid)


def _parse_inputted_alarm_clock(raw_alarm_clock):
    # Return a tuple (hour, minute) from the inputted alarm clock (i.e.
    # series of 4 digit).
    #
    # Raise a ValueError if invalid.
    if len(raw_alarm_clock) != 4:
        raise ValueError('invalid length: %s' % len(raw_alarm_clock))
    hour = int(raw_alarm_clock[:2])
    minute = int(raw_alarm_clock[2:])
    if hour >= 24:
        raise ValueError('invalid hour: %s', hour)
    if minute >= 60:
        raise ValueError('invalid minute: %s', minute)
    return hour, minute


def alarmclk_set(agi, cursor, args):
    userid = int(args[0])
    raw_alarm_clock = args[1]
    
    try:
        hour, minute = _parse_inputted_alarm_clock(raw_alarm_clock)
    except ValueError, e:
        logger.warning('Invalid alarm clock input for user %s: %s', e, userid)
        agi.set_variable('XIVO_ALARMCLK_OK', '0')
    else:
        alarm_clock = '%s:%s' % (hour, minute)
        _update_alarmclock_webi(userid, alarm_clock)
        agi.set_variable('XIVO_ALARMCLK_OK', '1')


def alarmclk_clear(agi, cursor, args):
    userid = int(args[0])
    
    cur_alarmclock = _get_alarmclock_db(cursor, userid)
    if cur_alarmclock:
        _update_alarmclock_webi(userid, '')
    else:
        logger.info('No alarm clock set for user %s', userid)


agid.register(alarmclk_pre_execute)
agid.register(alarmclk_set)
agid.register(alarmclk_clear)
