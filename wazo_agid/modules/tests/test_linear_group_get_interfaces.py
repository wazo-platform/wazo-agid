# Copyright 2015-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from hamcrest import assert_that, contains_inanyorder, has_properties
from xivo_dao.alchemy.queuemember import QueueMember

from wazo_agid.handlers.userfeatures import UserFeatures
from wazo_agid.modules import linear_group_get_interfaces


class TestGetGroupMembers(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_group_members_empty(self):
        with patch(
            'wazo_agid.modules.linear_group_get_interfaces.group_dao'
        ) as mock_dao:
            mock_dao.get.return_value = Mock(
                user_queue_members=[],
                extension_queue_members=[],
            )
            members = linear_group_get_interfaces.get_group_members(1)
            assert members == []

    def test_get_group_members_only_users(self):
        with patch(
            'wazo_agid.modules.linear_group_get_interfaces.group_dao'
        ) as mock_dao:
            mock_users = [
                Mock(
                    spec=QueueMember,
                    id='1',
                    user=Mock(spec=UserFeatures, uuid=str(uuid4())),
                ),
                Mock(
                    spec=QueueMember,
                    id='2',
                    user=Mock(spec=UserFeatures, uuid=str(uuid4())),
                ),
                Mock(
                    spec=QueueMember,
                    id='3',
                    user=Mock(spec=UserFeatures, uuid=str(uuid4())),
                ),
            ]
            mock_dao.get.return_value = Mock(
                user_queue_members=mock_users,
                extension_queue_members=[],
            )
            user_uuids = [member.user.uuid for member in mock_users]
            members = linear_group_get_interfaces.get_group_members(1)
            assert members and len(members) == 3
            assert_that(
                members,
                contains_inanyorder(
                    *(
                        has_properties(type='user', uuid=user_uuid)
                        for user_uuid in user_uuids
                    )
                ),
            )

    def test_get_group_members_only_extensions(self):
        with patch(
            'wazo_agid.modules.linear_group_get_interfaces.group_dao'
        ) as mock_dao:
            mock_extensions = [
                Mock(
                    spec=QueueMember,
                    id='1',
                    extension=Mock(exten='1', context='somecontext'),
                ),
                Mock(
                    spec=QueueMember,
                    id='2',
                    extension=Mock(exten='2', context='somecontext'),
                ),
                Mock(
                    spec=QueueMember,
                    id='3',
                    extension=Mock(exten='3', context='somecontext'),
                ),
            ]
            mock_dao.get.return_value = Mock(
                user_queue_members=[],
                extension_queue_members=mock_extensions,
            )

            members = linear_group_get_interfaces.get_group_members(1)
            assert members and len(members) == 3
            assert_that(
                members,
                contains_inanyorder(
                    *(
                        has_properties(
                            type='extension',
                            extension=member.extension.exten,
                            context='somecontext',
                        )
                        for member in mock_extensions
                    )
                ),
            )
