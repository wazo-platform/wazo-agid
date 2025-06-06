# Copyright 2012-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
from textwrap import dedent

import phonenumbers
from psycopg2.extras import DictCursor
from wazo_dird_client.client import DirdClient
from xivo_dao.resources.directory_profile import dao as directory_profile_dao

from wazo_agid import agid
from wazo_agid import dialplan_variables as dv
from wazo_agid import objects

logger = logging.getLogger(__name__)

FAKE_WAZO_USER_UUID = '00000000-0000-0000-0000-000000000000'


def callerid_forphones(agi: agid.FastAGI, cursor: DictCursor, args: list[str]) -> None:
    dird_client: DirdClient = agi.config['dird']['client']
    try:
        cid_name = agi.env['agi_calleridname']
        cid_number = agi.env['agi_callerid']

        logger.debug(
            'Resolving caller ID: incoming caller ID=%s %s', cid_name, cid_number
        )
        if not _should_reverse_lookup(cid_name, cid_number):
            return

        incall_id = int(agi.get_variable(dv.INCALL_ID))
        callee_info = directory_profile_dao.find_by_incall_id(incall_id)
        if callee_info is None:
            user_uuid = FAKE_WAZO_USER_UUID
        else:
            user_uuid = callee_info.user_uuid

        tenant_uuid = agi.get_variable('WAZO_TENANT_UUID')
        numbers = [cid_number]
        country = None
        try:
            tenant = objects.Tenant(agi, cursor, tenant_uuid)
            country = tenant.country
        except Exception as e:
            msg = f'Could not fetch tenant: {e}'
            logger.info(msg)
            agi.verbose(msg)

        if country:
            try:
                parsed_number = phonenumbers.parse(cid_number, country)

                numbers.append(
                    phonenumbers.format_number(
                        parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                    )
                )
                numbers.append(
                    phonenumbers.format_number(
                        parsed_number, phonenumbers.PhoneNumberFormat.E164
                    )
                )
                numbers.append(
                    phonenumbers.format_number(
                        parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL
                    )
                )
                numbers.append(
                    phonenumbers.format_out_of_country_calling_number(
                        parsed_number, region_calling_from=country
                    )
                )
                numbers.append(
                    phonenumbers.normalize_diallable_chars_only(
                        phonenumbers.format_number(
                            parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL
                        )
                    )
                )
            except phonenumbers.NumberParseException:
                logger.debug('Could not parse number %s', cid_number)

        query = {
            'query': dedent(
                '''
            query GetExtensFromUser($uuid: String!, $extens: [String!]!) {
                user(uuid: $uuid) {
                    contacts(profile: "default", extens: $extens) {
                        edges {
                            node {
                                wazoReverse
                            }
                        }
                    }
                }
            }'''
            ),
            'variables': {
                'uuid': user_uuid,
                'extens': numbers,
            },
        }
        response = dird_client.graphql.query(query, tenant_uuid=tenant_uuid)
        logger.debug('reverse lookup response: %s', response)

        if 'errors' in response:
            raise ValueError("Errors in GraphQL response: %s", response)

        reponse_user = response['data']['user']
        if not reponse_user:
            raise ValueError("No user data in GraphQL response")

        for edge in reponse_user['contacts']['edges']:
            node = edge.get('node')
            if not node:
                continue
            result = node.get('wazoReverse')
            if result is not None:
                logger.debug(
                    'Found caller ID from reverse lookup: "%s"<%s>',
                    result,
                    cid_number,
                )
                _set_new_caller_id(agi, result, cid_number)
                break
    except Exception as e:
        msg = f'Reverse lookup failed: {e}'
        logger.info(msg)
        agi.verbose(msg)


def is_phone_number(cid_name: str) -> bool:
    try:
        phonenumbers.parse(cid_name, None)
    except phonenumbers.phonenumberutil.NumberParseException as ex:
        # if error is due to country code not being recognized,
        # we can assume this is a national or local number format
        return (
            ex.error_type
            == phonenumbers.phonenumberutil.NumberParseException.INVALID_COUNTRY_CODE
        )
    else:
        return True


def _should_reverse_lookup(cid_name: str, cid_number: str) -> bool:
    return cid_name == 'unknown' or is_phone_number(cid_name)


def _set_new_caller_id(agi: agid.FastAGI, display_name: str, cid_number: str) -> None:
    new_caller_id = f'"{display_name}" <{cid_number}>'
    agi.set_callerid(new_caller_id)


def _set_reverse_lookup_variable(agi: agid.FastAGI, fields: dict[str, str]) -> None:
    agi.set_variable(dv.REVERSE_LOOKUP, _create_reverse_lookup_variable(fields))


def _create_reverse_lookup_variable(fields: dict[str, str]) -> str:
    variable_content = [f'db-{key}: {value}' for key, value in fields.items()]
    return ','.join(variable_content)


agid.register(callerid_forphones)
