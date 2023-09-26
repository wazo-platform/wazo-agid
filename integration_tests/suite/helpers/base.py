# Copyright 2022-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging

from pathlib import Path

from .agentd import AgentdMockClient
from .agid import AgidClient
from .confd import ConfdMockClient
from .calld import CalldMockClient
from .database import DbHelper
from .filesystem import FileSystemClient
from wazo_test_helpers.asset_launching_test_case import (
    AbstractAssetLaunchingHelper,
    cached_class_property,
    NoSuchPort,
    NoSuchService,
    WrongClient,
)
from wazo_test_helpers import until

DEFAULT_LOG_FORMAT = '%(asctime)s [%(process)d] (%(levelname)s) (%(name)s): %(message)s'
logging.basicConfig(format=DEFAULT_LOG_FORMAT)


class BaseAssetLaunchingHelper(AbstractAssetLaunchingHelper):
    assets_root = Path(__file__).parent / '..' / '..' / 'assets'
    asset = 'base'
    service = 'agid'

    @classmethod
    def reset_clients(cls):
        for attr in ('agid', 'db', 'calld', 'confd', 'agentd', 'filesystem'):
            delattr(cls, attr)
        until.true(cls.agid.is_ready, timeout=30)

    @classmethod
    def launch_service_with_asset(cls) -> None:
        """Make sure Agid service is up before starting first test."""
        super().launch_service_with_asset()
        until.true(cls.agid.is_ready, timeout=30)

    @cached_class_property
    def agid(cls) -> AgidClient:
        port = cls.service_port(4573, 'agid')
        return AgidClient('127.0.0.1', port)

    @cached_class_property
    def confd(cls) -> ConfdMockClient:
        port = cls.service_port('9486', 'confd')
        return ConfdMockClient('127.0.0.1', port, version='1.1')

    @cached_class_property
    def agentd(cls) -> AgentdMockClient:
        return AgentdMockClient('127.0.0.1', cls.service_port('9493', 'agentd'))

    @cached_class_property
    def calld(cls) -> CalldMockClient:
        return CalldMockClient('127.0.0.1', cls.service_port('9500', 'calld'))

    @cached_class_property
    def db(cls) -> DbHelper | WrongClient:
        try:
            port = cls.service_port(5432, 'postgres')
        except (NoSuchService, NoSuchPort):
            return WrongClient('postgres')

        # NOTE(fblackburn): Avoid importing wazo_agid and dependencies in tests,
        # since no database tests are needed
        return DbHelper.build(
            user='asterisk',
            password='proformatique',
            host='127.0.0.1',
            port=port,
            db='asterisk',
        )

    @cached_class_property
    def filesystem(cls) -> FileSystemClient:
        return FileSystemClient(execute=cls.docker_exec, service_name=cls.service)
