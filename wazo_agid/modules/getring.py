# -*- coding: utf-8 -*-
# Copyright 2006-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import ConfigParser
import logging

from wazo_agid import agid

CONFIG_FILE = "/etc/xivo/asterisk/xivo_ring.conf"
CONFIG_PARSER = None

logger = logging.getLogger(__name__)


def getring(agi, cursor, args):
    dstnum = agi.get_variable('XIVO_REAL_NUMBER')
    context = agi.get_variable('XIVO_REAL_CONTEXT')
    origin = agi.get_variable('XIVO_CALLORIGIN')
    referer = agi.get_variable('XIVO_FWD_REFERER').split(':', 1)[0]
    forwarded = agi.get_variable('XIVO_CALLFORWARDED')
    # TODO: maybe replace number@context with user id in conf file ?
    dstnum_context = "%s@%s" % (dstnum, context)
    referer_origin = "%s@%s" % (referer, origin)
    origin_fwd = "%s&forwarded" % origin
    referer_origin_fwd = "%s&forwarded" % referer_origin
    section = None

    if CONFIG_PARSER.has_option('number', "!%s" % dstnum_context):
        agi.set_variable('XIVO_RINGTYPE', "")
        return

    if len(dstnum) > 0 and CONFIG_PARSER.has_option('number', dstnum_context):
        section = CONFIG_PARSER.get('number', dstnum_context)

    logger.debug('Ring type available sections: "%s"', CONFIG_PARSER.sections())
    logger.debug('Ring type section: "%s"', section)
    logger.debug('Ring type context: "%s"', context)

    try:
        if section is None:
            section = CONFIG_PARSER.get('number', "@%s" % context)

        if section == 'number':
            raise ValueError("Invalid section name")

        if forwarded == '1' and CONFIG_PARSER.has_option(section, referer_origin_fwd):
            ringtype = CONFIG_PARSER.get(section, referer_origin_fwd)
        elif CONFIG_PARSER.has_option(section, referer_origin):
            ringtype = CONFIG_PARSER.get(section, referer_origin)
        elif forwarded == '1' and CONFIG_PARSER.has_option(section, origin_fwd):
            ringtype = CONFIG_PARSER.get(section, origin_fwd)
        elif forwarded == '1' and CONFIG_PARSER.has_option(section, 'forward'):
            ringtype = CONFIG_PARSER.get(section, 'forward')
        else:
            ringtype = CONFIG_PARSER.get(section, origin)

        phonetype = CONFIG_PARSER.get(section, 'phonetype')
    except (ConfigParser.NoOptionError, ValueError):
        logger.debug('Ring type exception', exc_info=True)
        agi.set_variable('XIVO_RINGTYPE', "")
        agi.verbose("Using the native phone ring tone")
    else:
        agi.set_variable('XIVO_RINGTYPE', ringtype)
        agi.set_variable('XIVO_PHONETYPE', phonetype)
        agi.verbose("Using ring tone %s" % (ringtype,))


def setup(cursor):
    global CONFIG_PARSER

    # This module is often called, keep this object alive.
    CONFIG_PARSER = ConfigParser.RawConfigParser()
    CONFIG_PARSER.readfp(open(CONFIG_FILE))


agid.register(getring, setup)
