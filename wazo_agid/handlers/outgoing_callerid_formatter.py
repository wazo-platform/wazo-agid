# Copyright 2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import phonenumbers

from wazo_agid import objects
from wazo_agid.handlers import handler


def _remove_none_numeric_char(raw: str) -> str:
    return ''.join(c for c in raw if c.isdigit())


class CallerIDFormatter(handler.Handler):
    def execute(self) -> None:
        self.set_caller_id()

    def set_caller_id(self) -> None:
        selected_cid = self._agi.get_variable('WAZO_SELECTED_CALLER_ID_TO_FORMAT')
        cid_format = self._agi.get_variable('TRUNK_OUTGOING_CALLER_ID_FORMAT')

        if not selected_cid:
            return

        if not cid_format:
            return

        number = phonenumbers.parse(selected_cid)
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
                f'Unknown supported TRUNCK_OUTGOING_CALLER_ID_FORMAT "{cid_format}"'
            )

        objects.CallerID.set(self._agi, formated_number)
