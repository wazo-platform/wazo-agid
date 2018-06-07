# -*- coding: utf-8 -*-
# Copyright (C) 2009-2014 Avencall
# SPDX-License-Identifier: GPL-3.0+

from xivo_agid import agid


def monitoring(agi, cursor, args):
    agi.send_command("Status: OK")

agid.register(monitoring)
