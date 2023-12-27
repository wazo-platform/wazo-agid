# Copyright 2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from psycopg2.extras import DictCursor

from wazo_agid import agid

logger = logging.getLogger(__name__)

VARIABLE_MAP = {
    'WAZO_CALLOPTIONS': 'XIVO_CALLOPTIONS',
}
ORIG_VALUE_TPL = 'WAZO_COMPAT_{new_name}_ORIG'


def pre_subroutine_compat(
    agi: agid.FastAGI, cursor: DictCursor, args: list[str]
) -> None:
    logger.debug('Entering pre-subroutine compatibility')
    for new_name, old_name in VARIABLE_MAP.items():
        current_value = agi.get_variable(new_name)
        agi.set_variable(old_name, current_value)
        agi.set_variable(ORIG_VALUE_TPL.format(new_name=new_name), current_value)


def post_subroutine_compat(
    agi: agid.FastAGI, cursor: DictCursor, args: list[str]
) -> None:
    logger.debug('Entering post-subroutine compatibility')
    for new_name, old_name in VARIABLE_MAP.items():
        orig_value = agi.get_variable(ORIG_VALUE_TPL.format(new_name=new_name))
        new_value = agi.get_variable(new_name)
        compat_value = agi.get_variable(old_name)

        # Cleanup the mess to make sure it does not get used
        agi.set_variable(old_name, '')
        agi.set_variable(ORIG_VALUE_TPL.format(new_name=new_name), '')

        # Nothing changed, keep going
        if new_value == orig_value == compat_value:
            continue

        # New name has been used everything is fine
        if new_value != orig_value:
            continue

        # The old variable name has been used
        if compat_value != orig_value:
            msg = (
                f'The {old_name} variable has been modified by a subroutine.'
                f' Use {new_name} instead'
            )
            logger.info(msg)
            agi.verbose(msg)
            agi.set_variable(new_name, compat_value)


agid.register(pre_subroutine_compat)
agid.register(post_subroutine_compat)
