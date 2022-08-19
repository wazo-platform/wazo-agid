# Copyright 2006-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import re

logger = logging.getLogger(__name__)

RIGHTCALL_AUTHORIZATION_COLNAME = "rightcall.authorization"
RIGHTCALL_PASSWD_COLNAME = "rightcall.passwd"

rep = (('_', ''),
       ('*', '\*'),
       ('+', '\+'),
       ('X', '[0-9]'),
       ('Z', '[1-9]'),
       ('N', '[2-9]'),
       ('.', '[0-9#\*]+'),
       ('!', '[0-9#\*]*'))


class RuleAppliedException(Exception):
    pass


def allow(agi):
    agi.set_variable('XIVO_AUTHORIZATION', "ALLOW")
    raise RuleAppliedException()


def deny(agi, password):
    if password:
        agi.set_variable('XIVO_PASSWORD', password)

    agi.set_variable('XIVO_AUTHORIZATION', "DENY")
    raise RuleAppliedException()


def extension_matches(number, pattern):
    for (key, val) in rep:
        pattern = pattern.replace(key, val)

    return bool(re.match("^%s$" % pattern, number))


def apply_rules(agi, rules):
    if not rules:
        return

    for rule in rules:
        if rule[RIGHTCALL_AUTHORIZATION_COLNAME]:
            allow(agi)

    deny(agi, rule[RIGHTCALL_PASSWD_COLNAME])
