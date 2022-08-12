# Copyright 2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
import os
import unittest

from .agentd import AgentdMockClient
from .agid import AgidClient
from .confd import ConfdMockClient
from .database import DbHelper
from .filesystem import FileSystemClient
from wazo_test_helpers.asset_launching_test_case import (
    AssetLaunchingTestCase,
    NoSuchPort,
    NoSuchService,
    WrongClient,
)

use_asset = pytest.mark.usefixtures


class BaseAssetLaunchingTestCase(AssetLaunchingTestCase):

    assets_root = os.path.join(os.path.dirname(__file__), '../..', 'assets')
    asset = 'base'
    service = 'agid'

    @classmethod
    def make_agid(cls):
        port = cls.service_port(4573, 'agid')
        return AgidClient('127.0.0.1', port)

    @classmethod
    def make_confd(cls):
        return ConfdMockClient('127.0.0.1', cls.service_port('9486', 'confd'), version='1.1')

    @classmethod
    def make_agentd(cls):
        return AgentdMockClient('127.0.0.1', cls.service_port('9493', 'agentd'))

    @classmethod
    def make_database(cls):
        try:
            port = cls.service_port(5432, 'postgres')
        except (NoSuchService, NoSuchPort):
            return WrongClient('postgres')

        # NOTE(fblackburn): Avoid to import wazo_agid and dependencies in tests,
        # since no database tests are needed
        return DbHelper.build(
            user='asterisk',
            password='proformatique',
            host='127.0.0.1',
            port=port,
            db='asterisk',
        )


class IntegrationTest(unittest.TestCase):
    asset_cls = BaseAssetLaunchingTestCase

    @classmethod
    def setUpClass(cls):
        cls.reset_clients()

    @classmethod
    def reset_clients(cls):
        cls.agid = cls.asset_cls.make_agid()
        cls.db = cls.asset_cls.make_database()
        cls.confd = cls.asset_cls.make_confd()
        cls.agentd = cls.asset_cls.make_agentd()
        cls.filesystem = FileSystemClient(
            execute=cls.asset_cls.docker_exec,
            service_name=cls.asset_cls.service,
        )

