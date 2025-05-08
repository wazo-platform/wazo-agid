# Copyright 2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging

import phonenumbers
from psycopg2.extras import DictCursor
from xivo_dao.resources.user import dao as user_dao

from wazo_agid import agid

logger = logging.getLogger(__name__)


def interpret_number(number: str, country: str | None) -> phonenumbers.PhoneNumber:
    try:
        return phonenumbers.parse(number, country)
    except phonenumbers.NumberParseException as ex:
        logger.debug(
            'number %s cannot be parsed as a valid number from country %s: %s',
            number,
            country,
            str(ex),
        )
    try:
        return phonenumbers.parse('+' + number, None)
    except phonenumbers.NumberParseException as ex:
        logger.debug(
            'number %s cannot be parsed as a valid number international number +%s: %s',
            number,
            number,
            str(ex),
        )

        if country:
            raise

    country = country or 'FR'
    logger.debug('Trying to parse number %s with default country %s', number, country)
    try:
        return phonenumbers.parse(number, country)
    except phonenumbers.NumberParseException as ex:
        logger.debug(
            'number %s cannot be parsed as a valid number from default country %s: %s',
            number,
            country,
            str(ex),
        )
        raise


def screen_blocklist(agi: agid.FastAGI, cursor: DictCursor, args: list[str]) -> None:
    confd_client = agi.config['confd']['client']

    # get caller id number
    caller_id_number = agi.get_variable('CALLERID(num)')
    if not caller_id_number:
        return

    # get wazo user uuid
    if len(args) < 1 or not (user_uuid := args[0]):
        logger.error('user_uuid argument missing')
        return

    # get user's country for number interpretation
    user = user_dao.get_by(uuid=user_uuid)
    user_country = user.country
    user_tenant_uuid = user.tenant_uuid

    logger.debug(
        'screening caller id number %s calling user %s (country=%s)',
        caller_id_number,
        user_uuid,
        user_country,
    )

    try:
        number = interpret_number(caller_id_number, user_country)
    except phonenumbers.NumberParseException as ex:
        logger.error(
            'Failed to screen number %s with blocklist of user %s: %s',
            caller_id_number,
            user_uuid,
            str(ex),
        )
        return

    e164_number = phonenumbers.format_number(
        number, phonenumbers.PhoneNumberFormat.E164
    )
    logger.debug('Looking up number %s in blocklist of user %s', e164_number, user_uuid)
    # lookup caller id number in wazo-confd blocklist API
    result = confd_client.users(user_uuid).blocklist.numbers.lookup(
        number_exact=e164_number,
        tenant_uuid=user_tenant_uuid,
    )
    if result:
        logger.debug(
            'Caller ID number %s is blocked by user %s(blocklist number uuid=%s)',
            caller_id_number,
            user_uuid,
            result,
        )
        agi.set_variable('WAZO_BLOCKED_NUMBER_UUID', result)


agid.register(screen_blocklist)
