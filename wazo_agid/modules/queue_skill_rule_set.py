# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import json

from psycopg2.extras import DictCursor
from xivo_dao.alchemy.queueskillrule import QueueSkillRule
from xivo_dao.helpers.db_utils import session_scope

from wazo_agid import agid


def queue_skill_rule_set(
    agi: agid.FastAGI, cursor: DictCursor, args: list[str]
) -> None:
    actionarg2 = agi.get_variable('ARG2')
    options = actionarg2.split(';') if actionarg2 else []

    timeout = ''
    call = agi.get_variable('XIVO_QUEUESKILLRULESET')
    skill_rule_id: str | None = None
    skill_rule_variables: str | None = None

    if len(options) == 1:
        timeout = options[0]
    elif len(options) == 2:
        skill_rule_id = options[0]
        skill_rule_variables = options[1]
    elif len(options) == 3:
        timeout = options[0]
        skill_rule_id = options[1]
        skill_rule_variables = options[2]

    if not skill_rule_id:
        _set_variables(agi, call, timeout)
        return

    with session_scope() as session:
        skill_rule = session.query(QueueSkillRule).get(int(skill_rule_id))
        if not skill_rule:
            _set_variables(agi, call, timeout)
            return

        skill_rule_function = f'skillrule-{skill_rule.id}'
        skill_rule_kwargs = []
        if skill_rule_variables:
            skill_rule_variables = skill_rule_variables.replace('|', ',')
            skill_rules_dict: dict[str, str] = json.loads(skill_rule_variables)
            skill_rule_kwargs = [
                f'{key}={value}' for key, value in skill_rules_dict.items()
            ]
        call = f'{skill_rule_function}({",".join(skill_rule_kwargs)})'

    _set_variables(agi, call, timeout)


def _set_variables(agi: agid.FastAGI, call: str, timeout: str) -> None:
    agi.set_variable('XIVO_QUEUESKILLRULESET', call)
    agi.set_variable('ARG2_TIMEOUT', timeout)


agid.register(queue_skill_rule_set)
