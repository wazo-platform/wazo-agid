# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
import os
import unittest

from .agid import AgidClient
from xivo_test_helpers.asset_launching_test_case import AssetLaunchingTestCase

use_asset = pytest.mark.usefixtures


class BaseAssetLaunchingTestCase(AssetLaunchingTestCase):

    assets_root = os.path.join(os.path.dirname(__file__), '../..', 'assets')
    asset = 'base'
    service = 'agid'

    @classmethod
    def make_agid(cls):
        port = cls.service_port(4573, 'agid')
        return AgidClient('127.0.0.1', port)


class IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reset_clients()

    @classmethod
    def reset_clients(cls):
        cls.agid = BaseAssetLaunchingTestCase.make_agid()
