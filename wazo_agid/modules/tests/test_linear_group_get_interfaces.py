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

    def test_get_group_info_empty(self):
        with patch(
            'wazo_agid.modules.linear_group_get_interfaces.group_dao'
        ) as mock_dao:
            mock_dao.get.return_value = Mock(
                user_queue_members=[],
                extension_queue_members=[],
                ring_in_use=False,
            )
            mock_dao.get.return_value.name = 'test'
            group_info = linear_group_get_interfaces.get_group_info(1)
            assert group_info.members == []
            assert group_info.name == 'test'
            assert not group_info.ring_in_use

    def test_get_group_info_only_users(self):
        with patch(
            'wazo_agid.modules.linear_group_get_interfaces.group_dao'
        ) as mock_dao:
            mock_users = [
                Mock(
                    spec=QueueMember,
                    id='1',
                    user=Mock(spec=UserFeatures, uuid=str(uuid4()), enablednd=False),
                ),
                Mock(
                    spec=QueueMember,
                    id='2',
                    user=Mock(spec=UserFeatures, uuid=str(uuid4()), enablednd=True),
                ),
                Mock(
                    spec=QueueMember,
                    id='3',
                    user=Mock(spec=UserFeatures, uuid=str(uuid4()), enablednd=False),
                ),
            ]
            mock_dao.get.return_value = Mock(
                user_queue_members=mock_users,
                extension_queue_members=[],
            )
            group_info = linear_group_get_interfaces.get_group_info(1)
            assert group_info.members and len(group_info.members) == 3
            assert_that(
                group_info.members,
                contains_inanyorder(
                    *(
                        has_properties(
                            type='user',
                            uuid=member.user.uuid,
                            dnd=member.user.enablednd,
                        )
                        for member in mock_users
                    )
                ),
            )

    def test_get_group_info_only_extensions(self):
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

            group_info = linear_group_get_interfaces.get_group_info(1)
            assert group_info.members and len(group_info.members) == 3
            assert_that(
                group_info.members,
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
