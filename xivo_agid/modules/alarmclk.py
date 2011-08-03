# -*- coding: UTF-8 -*-

__version__ = "$Revision$ $Date$"
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

import logging
from xivo_agid import agid
from xivo_agid import objects

logger = logging.getLogger(__name__)


def _update_alarmclock(cursor, userid, alarm_clock):
    # Update the alarm clock for a given user
    cursor.query("UPDATE userfeatures "
                 "SET alarmclock = %s "
                 "WHERE id = %s",
                 parameters=(alarm_clock, userid))


def _clear_alarmclock(cursor, userid):
    # Equivalent to "_update_alarmclock(cursor, userid, '')" 
    _update_alarmclock(cursor, userid, '')


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
    
    _clear_alarmclock(cursor, userid)
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
        _update_alarmclock(cursor, userid, alarm_clock)
        agi.set_variable('XIVO_ALARMCLK_OK', '1')


def alarmclk_clear(agi, cursor, args):
    userid = int(args[0])
    
    _clear_alarmclock(cursor, userid)


agid.register(alarmclk_pre_execute)
agid.register(alarmclk_set)
agid.register(alarmclk_clear)
