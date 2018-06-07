# -*- coding: utf-8 -*-
# Copyright (C) 2012-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

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
