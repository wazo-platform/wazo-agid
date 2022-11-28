# Copyright 2006-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import configparser
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
    dstnum_context = f"{dstnum}@{context}"
    referer_origin = f"{referer}@{origin}"
    origin_fwd = f"{origin}&forwarded"
    referer_origin_fwd = f"{referer_origin}&forwarded"
    section = None

    agi.set_variable('XIVO_RINGTYPE', "")

    if CONFIG_PARSER.has_option('number', f"!{dstnum_context}"):
        return

    if len(dstnum) > 0 and CONFIG_PARSER.has_option('number', dstnum_context):
        section = CONFIG_PARSER.get('number', dstnum_context)

    logger.debug('Ring type available sections: "%s"', CONFIG_PARSER.sections())
    logger.debug('Ring type section: "%s"', section)
    logger.debug('Ring type context: "%s"', context)

    try:
        if section is None:
            try:
                section = CONFIG_PARSER.get('number', f"@{context}")
            except configparser.NoOptionError:
                return

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
    except (configparser.NoOptionError, ValueError):
        logger.debug('Ring type exception', exc_info=True)
        agi.verbose("Using the native phone ring tone")
    else:
        agi.set_variable('XIVO_RINGTYPE', ringtype)
        agi.set_variable('XIVO_PHONETYPE', phonetype)
        agi.verbose(f"Using ring tone {ringtype}")


def setup(cursor):
    global CONFIG_PARSER

    # This module is often called, keep this object alive.
    CONFIG_PARSER = configparser.RawConfigParser()
    CONFIG_PARSER.readfp(open(CONFIG_FILE))


agid.register(getring, setup)
