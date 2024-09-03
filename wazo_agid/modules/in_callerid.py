# Copyright 2006-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import re
import sys
from configparser import NoOptionError, RawConfigParser

from psycopg2.extras import DictCursor

from wazo_agid import agid

RULES_FILE = '/etc/xivo/asterisk/xivo_in_callerid.conf'

log = logging.getLogger('wazo_agid.modules.in_callerid')
config: RawConfigParser = None  # type: ignore[assignment]
re_objs: dict[str, re.Pattern] = {}


def in_callerid(agi: agid.FastAGI, cursor: DictCursor, args: list[str]) -> None:
    callerid_num = agi.env['agi_callerid']
    callerid_name = agi.env['agi_calleridname']
    same_cid = callerid_num == callerid_name

    for section_name in config.sections():
        log.debug('section `%s`', section_name)
        re_obj = re_objs[section_name]

        if not re_obj.match(callerid_num):
            log.debug('pattern `%s` does not match `%s`', re_obj.pattern, callerid_num)
            continue

        log.debug('pattern `%s` matches `%s`', re_obj.pattern, callerid_num)
        if config.has_option(section_name, 'strip'):
            str_strip = config.get(section_name, 'strip')
            log.debug('stripping `%s` digits from `%s`', str_strip, callerid_num)

            if str_strip.isdigit():
                strip = int(str_strip)

                if strip > 0:
                    callerid_num = callerid_num[strip:]

        if config.has_option(section_name, 'add'):
            add = config.get(section_name, 'add')
            log.debug('prefixing `%s` with `%s`', callerid_num, add)

            if add:
                callerid_num = add + callerid_num

        if same_cid:
            agi.set_variable('CALLERID(all)', f'"{callerid_num}" <{callerid_num}>')
        else:
            agi.set_variable('CALLERID(num)', callerid_num)

        return


def setup(cursor: DictCursor) -> None:
    global config

    re_objs.clear()
    config = RawConfigParser()
    config.read([RULES_FILE])

    for section_name in config.sections():
        try:
            regexp = config.get(section_name, 'callerid')
        except NoOptionError:
            log.error("option 'callerid' not found in section %r", section_name)
            sys.exit(1)

        try:
            re_obj = re.compile(regexp)
        except re.error:
            log.error("invalid regexp %r in section %r", regexp, section_name)
            sys.exit(1)

        re_objs[section_name] = re_obj


agid.register(in_callerid, setup)
