# Copyright 2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import re

import phonenumbers

from wazo_agid import objects
from wazo_agid.handlers import handler

VALID_PHONE_NUMBER_RE = re.compile(r'^\+?\d{3,15}$')


def _remove_none_numeric_char(raw: str) -> str:
    return ''.join(c for c in raw if c.isdigit())


class CallerIDFormatter(handler.Handler):
    def execute(self) -> None:
        self.set_caller_id()

    def set_caller_id(self) -> None:
        selected_cid = self._agi.get_variable('WAZO_SELECTED_CALLER_ID_TO_FORMAT')
        cid_format = self._agi.get_variable('TRUNK_OUTGOING_CALLER_ID_FORMAT')
        tenant_country = self._agi.get_variable('WAZO_TENANT_COUNTRY')

        if not selected_cid:
            return

        if not cid_format:
            return

        try:
            number = phonenumbers.parse(selected_cid, tenant_country)
        except phonenumbers.phonenumberutil.NumberParseException:
            self._set_raw_number(selected_cid)
        else:
            self._set_formated_number(number, cid_format)

    def _set_raw_number(self, selected_number: str) -> None:
        matches = VALID_PHONE_NUMBER_RE.match(selected_number)
        if matches:
            objects.CallerID.set(self._agi, selected_number)
        else:
            self._agi.verbose('Ignoring selected caller ID')

    def _set_formated_number(self, number, cid_format: str) -> None:
        if cid_format == 'national':
            formated_number = _remove_none_numeric_char(
                phonenumbers.format_number(
                    number,
                    phonenumbers.PhoneNumberFormat.NATIONAL,
                )
            )
        elif cid_format == 'E164':
            formated_number = _remove_none_numeric_char(
                phonenumbers.format_number(
                    number,
                    phonenumbers.PhoneNumberFormat.E164,
                )
            )
        elif cid_format == '+E164':
            formated_number = phonenumbers.format_number(
                number,
                phonenumbers.PhoneNumberFormat.E164,
            )
        else:
            self._agi.verbose(
                f'Unknown supported TRUNK_OUTGOING_CALLER_ID_FORMAT "{cid_format}"'
            )
        objects.CallerID.set(self._agi, formated_number)
