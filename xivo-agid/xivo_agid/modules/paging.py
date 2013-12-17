# -*- coding: utf-8 -*-

# Copyright (C) 2012-2013 Avencall
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
from xivo_agid import objects

logger = logging.getLogger(__name__)


def paging(agi, cursor, args):

    userid = agi.get_variable('XIVO_USERID')

    try:
        paging_entry = objects.Paging(agi,
                                      cursor,
                                      args[0],
                                      userid)
    except (ValueError, LookupError), e:
        agi.answer()
        agi.stream_file('vm-incorrect')
        agi.dp_break('Sorry you are not authorize to page this group : %s' % str(e))

    paging_line = '&'.join(paging_entry.lines)

    agi.set_variable('XIVO_PAGING_LINES', paging_line)
    agi.set_variable('XIVO_PAGING_TIMEOUT', paging_entry.timeout)

    # s = call phones only if not busy
    paging_opts = 's'

    if paging_entry.duplex:
        paging_opts = paging_opts + 'd'

    if paging_entry.quiet:
        paging_opts = paging_opts + 'q'

    if paging_entry.record:
        paging_opts = paging_opts + 'r'

    if paging_entry.ignore:
        paging_opts = paging_opts + 'i'

    if paging_entry.announcement_play:
        paging_dir_sound = '/var/lib/xivo/sounds/playback'
        paging_opts = paging_opts + 'A(%s/%s)' % (paging_dir_sound, paging_entry.announcement_file)

    if paging_entry.announcement_caller:
        paging_opts = paging_opts + 'n'

    agi.set_variable('XIVO_PAGING_OPTS', paging_opts)

agid.register(paging)
