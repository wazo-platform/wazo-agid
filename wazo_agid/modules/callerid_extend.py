# Copyright 2012-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_agid import agid


def callerid_extend(agi, cursor, args):
    if 'agi_callington' in agi.env:
        agi.set_variable('XIVO_SRCTON', agi.env['agi_callington'])


agid.register(callerid_extend)
