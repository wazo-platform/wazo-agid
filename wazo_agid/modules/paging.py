# -*- coding: utf-8 -*-
# Copyright 2012-2020 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import os

from wazo_agid import agid
from wazo_agid import objects

logger = logging.getLogger(__name__)


def paging(agi, cursor, args):

    userid = agi.get_variable('XIVO_USERID')

    try:
        paging_entry = objects.Paging(agi,
                                      cursor,
                                      args[0],
                                      userid)
    except (ValueError, LookupError) as e:
        agi.answer()
        agi.stream_file('vm-incorrect')
        agi.dp_break('Sorry you are not authorize to page this group : %s' % str(e))

    # TODO PJSIP migration
    lines = []
    for line in paging_entry.lines:
        if line.startswith('SIP/'):
            lines.append('PJ{}'.format(line))
        else:
            lines.append(line)

    paging_line = '&'.join(lines)

    agi.set_variable('XIVO_PAGING_LINES', paging_line)
    agi.set_variable('XIVO_PAGING_TIMEOUT', paging_entry.timeout)

    # s = call phones only if not busy
    # b = Gosub for each destination channels
    paging_opts = 'sb(paging^add-sip-headers^1)'

    if paging_entry.duplex:
        paging_opts = paging_opts + 'd'

    if paging_entry.quiet:
        paging_opts = paging_opts + 'q'

    if paging_entry.record:
        paging_opts = paging_opts + 'r'

    if paging_entry.ignore:
        paging_opts = paging_opts + 'i'

    if paging_entry.announcement_play and paging_entry.announcement_file:
        announcement_file_name = os.path.join('/var/lib/wazo/sounds/tenants',
                                              paging_entry.tenant_uuid,
                                              'playback',
                                              paging_entry.announcement_file)
        paging_opts = paging_opts + 'A({file_name})'.format(file_name=announcement_file_name)

    if paging_entry.announcement_caller:
        paging_opts = paging_opts + 'n'

    agi.set_variable('XIVO_PAGING_OPTS', paging_opts)


agid.register(paging)
