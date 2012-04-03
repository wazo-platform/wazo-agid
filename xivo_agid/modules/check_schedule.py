# -*- coding: utf-8 -*-

__license__ = """
    Copyright (C) 2010-2012  Avencall

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


def check_schedule(agi, cursor, args):
    path = agi.get_variable('XIVO_PATH')
    pathid = agi.get_variable('XIVO_PATH_ID')

    if not path:
        return

    objects.Schedule(agi, cursor, path=path, pathid=pathid)

    # erase path for next schedule check
    agi.set_variable('XIVO_PATH', '')


agid.register(check_schedule)
