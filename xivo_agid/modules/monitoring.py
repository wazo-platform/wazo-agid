# -*- coding: utf-8 -*-
# Copyright 2009-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from xivo_agid import agid


def monitoring(agi, cursor, args):
    agi.send_command("Status: OK")


agid.register(monitoring)
