# Copyright 2024-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
import re

from xivo.reverse_lookup import format_phone_number_e164, format_phone_number_national

from wazo_agid import dialplan_variables as dv
from wazo_agid import objects
from wazo_agid.handlers import handler

VALID_PHONE_NUMBER_RE = re.compile(r'^\+?\d{3,15}$')
CALLER_ID_ALL_REGEX = re.compile(r'^"(.*)" <(\+?\d{3,15})>$')


logger = logging.getLogger(__name__)


def _remove_non_numeric_char(raw: str) -> str:
    return ''.join(c for c in raw if c.isdigit())


class CallerIDFormatter(handler.Handler):
    def execute(self) -> None:
        self.cid_format = self._agi.get_variable(dv.TRUNK_CID_FORMAT)
        self.tenant_country = self._agi.get_variable('WAZO_TENANT_COUNTRY')
        if self.cid_format:
            self.set_caller_id()

        extern_num = self._agi.get_variable(dv.DST_REDIRECTING_EXTERN_NUM)
        if extern_num:
            self.set_diversion(extern_num)

    def set_caller_id(self) -> None:
        selected_cid = self._agi.get_variable(dv.SELECTED_CALLER_ID)

        if not selected_cid:
            return

        matches = CALLER_ID_ALL_REGEX.match(selected_cid)
        if matches:
            cid_name = matches.group(1)
            cid_number = matches.group(2)
        else:
            cid_name = ''
            cid_number = selected_cid

        formatted_cid_number = self._format_number(cid_number)
        if not formatted_cid_number:
            logger.info(
                'caller id number %s cannot be parsed '
                'as a valid number for tenant country %s',
                cid_number,
                self.tenant_country,
            )
            self._set_raw_number(cid_name, cid_number)
        else:
            self._set_caller_id(cid_name, formatted_cid_number)

    def set_diversion(self, extern_num) -> None:
        extern_name = self._agi.get_variable('WAZO_DST_REDIRECTING_EXTERN_NAME')
        logger.debug(
            'country: %s\tnum: %s\tname:%s',
            self.tenant_country,
            extern_num,
            extern_name,
        )

        formatted_extern_num = self._format_number(extern_num)
        if not formatted_extern_num:
            logger.debug(
                'could not format number "%s" to %s',
                extern_num,
                self.cid_format,
            )
            self._agi.set_variable('REDIRECTING(from-num,i)', extern_num)
        else:
            self._agi.set_variable('REDIRECTING(from-num,i)', formatted_extern_num)
        self._agi.set_variable('REDIRECTING(from-name,i)', extern_name)

    def _set_raw_number(self, name: str, number: str) -> None:
        matches = VALID_PHONE_NUMBER_RE.match(number)
        if matches:
            self._set_caller_id(name, number)
        else:
            self._agi.verbose(
                f'Ignoring selected caller ID {number} not matching supported pattern'
            )

    def _format_number(self, number: str) -> str | None:
        if self.cid_format == 'national':
            formatted_num = format_phone_number_national(number, self.tenant_country)
            formatted_num = (
                _remove_non_numeric_char(formatted_num) if formatted_num else None
            )
        elif self.cid_format == 'E164':
            formatted_num = format_phone_number_e164(number, self.tenant_country)
            formatted_num = (
                _remove_non_numeric_char(formatted_num) if formatted_num else None
            )
        elif self.cid_format == '+E164':
            formatted_num = format_phone_number_e164(number, self.tenant_country)
        else:
            self._agi.verbose(f'Unsupported {dv.TRUNK_CID_FORMAT} "{self.cid_format}"')
        return formatted_num

    def _set_caller_id(self, name: str, number: str) -> None:
        if name:
            objects.CallerID.set(self._agi, f'"{name}" <{number}>')
        else:
            objects.CallerID.set(self._agi, number)
