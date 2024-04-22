# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from xivo_dao.alchemy.groupfeatures import GroupFeatures
from xivo_dao.resources.group import dao as group_dao

from wazo_agid import agid

if TYPE_CHECKING:
    from psycopg2.extras import DictCursor

    from wazo_agid.agid import FastAGI


logger = logging.getLogger(__name__)


@dataclass
class UserMemberInfo:
    uuid: str
    type: Literal['user'] = 'user'


@dataclass
class ExtensionMemberInfo:
    extension: str
    context: str
    type: Literal['extension'] = 'extension'


def build_user_interface(user_uuid: str, user_interfaces):
    return f'Local/{user_uuid}@userlineslineargroup'


def build_extension_interface(extension: str, context: str):
    return f'Local/{extension}@{context}'


def get_group_members(group_id: int) -> list[UserMemberInfo | ExtensionMemberInfo]:
    group: GroupFeatures = group_dao.get(group_id=group_id)

    user_member_info = [
        UserMemberInfo(
            uuid=user_member.user.uuid,
        )
        for user_member in group.user_queue_members
    ]

    extension_member_info = [
        ExtensionMemberInfo(
            extension=extension_member.extension.exten,
            context=extension_member.extension.context,
        )
        for extension_member in group.extension_queue_members
    ]

    return user_member_info + extension_member_info


def linear_group_get_interfaces(
    agi: FastAGI, cursor: DictCursor, args: list[str]
) -> None:
    group_id = int(args[0])
    members = get_group_members(group_id)
    # TODO: sort members with users first
    for i, member in enumerate(members):
        if member.type == 'user':
            # TODO: implement dispatch to wake_mobile, direct dial multiple interfaces
            # user_interfaces = _UserLine(agi, member['uuid']).interfaces

            agi.set_variable(
                f'WAZO_GROUP_LINEAR_{i}_INTERFACE',
                build_user_interface(member.uuid, ()),
            )
        elif member.type == 'extension':
            agi.set_variable(
                f'WAZO_GROUP_LINEAR_{i}_INTERFACE',
                build_extension_interface(member.extension, member.context),
            )


agid.register(linear_group_get_interfaces)
