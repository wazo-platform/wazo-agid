# Copyright 2020-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from unittest import TestCase
from unittest.mock import Mock
from hamcrest import assert_that, equal_to

from ..paging import build_options


class TestPagingOptions(TestCase):
    def test_build_options_nothing_set(self):
        paging = Mock(
            duplex=False,
            quiet=False,
            record=False,
            ignore=False,
            announcement_play=False,
            announcement_file=None,
            announcement_caller=False,
        )

        options = build_options(paging)

        assert_that(options, equal_to('sb(paging^add-sip-headers^1)'))

    def test_build_options_all(self):
        paging = Mock(
            duplex=True,
            quiet=True,
            record=True,
            ignore=True,
            announcement_play=True,
            announcement_file='filename',
            announcement_caller=True,
            tenant_uuid='<tenant_uuid>',
        )

        options = build_options(paging)

        assert_that(
            options,
            equal_to(
                'sb(paging^add-sip-headers^1)dqriA'
                '(/var/lib/wazo/sounds/tenants/<tenant_uuid>/playback/filename)n'
            ),
        )

    def test_build_options_announcement_play_no_file(self):
        paging = Mock(
            duplex=False,
            quiet=False,
            record=False,
            ignore=False,
            announcement_play=True,
            announcement_file=None,
            announcement_caller=False,
        )

        options = build_options(paging)

        assert_that(options, equal_to('sb(paging^add-sip-headers^1)'))
