# Copyright 2021-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from collections.abc import Generator

import pytest
from wazo_test_helpers.asset_launching_test_case import make_asset_fixture

from .helpers.base import BaseAssetLaunchingHelper


@pytest.fixture(scope='session')
def base_asset() -> Generator[BaseAssetLaunchingHelper, None, None]:
    yield from make_asset_fixture(BaseAssetLaunchingHelper)
