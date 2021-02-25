# -*- coding: utf-8 -*-
# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_agid import agid
from wazo_agid.handlers import queue


def queue_answered_call(agi, cursor, args):
    handler = queue.AnswerHandler(agi, cursor, args)
    handler.execute()


agid.register(queue_answered_call)
