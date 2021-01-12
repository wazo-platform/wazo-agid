# -*- coding: utf-8 -*-
# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import re

from wazo_agid import agid
from wazo_agid.dialplan_variables import CALL_OPTIONS

B_REGEX = re.compile(r'b\(([\-_0-9A-Za-z]+)\^?.*?\)')


# This AGI was added in 21.01 to avoid breaking user written dialplan
# This AGI and all of it's calls should be deleted in a reasonable amount of time 22.01?
def convert_pre_dial_handler(agi, cursor, args):
    call_options = agi.get_variable(CALL_OPTIONS)
    if not call_options:
        return

    match = B_REGEX.search(call_options)
    if not match:
        return

    to_remove = match.group(0)
    to_stack = match.group(1)

    agi.verbose('WARNING: deprecated dialplan option detected {}'.format(to_stack))
    agi.verbose('Wazo pre-dial handlers should be used instead')

    pruned_call_options = call_options.replace(to_remove, '')
    agi.set_variable(CALL_OPTIONS, pruned_call_options)

    new_handler = '{},s,1'.format(to_stack)
    agi.set_variable('PUSH(_WAZO_PRE_DIAL_HANDLERS,|)', new_handler)


agid.register(convert_pre_dial_handler)
