# -*- coding: utf-8 -*-
# Copyright 2006-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import re
import sys
import logging
import ConfigParser

from wazo_agid import agid

RULES_FILE = '/etc/xivo/asterisk/xivo_in_callerid.conf'

log = logging.getLogger('wazo_agid.modules.in_callerid')
config = None
re_objs = {}


def in_callerid(agi, cursor, args):
    callerid_num = agi.env['agi_callerid']
    callerid_name = agi.env['agi_calleridname']
    same_cid = callerid_num == callerid_name

    for section in config.sections():
        section_name = section.get_name()
        log.debug('section `%s`', section_name)
        re_obj = re_objs[section_name]

        if not re_obj.match(callerid_num):
            log.debug('pattern `%s` does not match `%s`', re_obj.pattern, callerid_num)
            continue

        log.debug('pattern `%s` matches `%s`', re_obj.pattern, callerid_num)
        if section.has_option('strip'):
            str_strip = section.get('strip')
            log.debug('stripping `%s` digits from `%s`', str_strip, callerid_num)

            if str_strip.isdigit():
                strip = int(str_strip)

                if strip > 0:
                    callerid_num = callerid_num[strip:]

        if section.has_option('add'):
            add = section.get('add')
            log.debug('prefixing `%s` with `%s`', callerid_num, add)

            if add:
                callerid_num = add + callerid_num

        if same_cid:
            agi.set_callerid(callerid_num)
        else:
            agi.set_variable('CALLERID(num)', callerid_num)

        return


def setup(cursor):
    global config

    re_objs.clear()
    config = ConfigParser.RawConfigParser()
    config.read([RULES_FILE])

    for section in config.sections():
        try:
            regexp = section.get('callerid')
        except ConfigParser.NoOptionError:
            log.error("option 'callerid' not found in section %r", section.get_name())
            sys.exit(1)

        try:
            re_obj = re.compile(regexp)
        except re.error:
            log.error("invalid regexp %r in section %r", regexp, section.get_name())
            sys.exit(1)

        re_objs[section.get_name()] = re_obj


agid.register(in_callerid, setup)
