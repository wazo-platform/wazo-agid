# -*- coding: utf-8 -*-
# Copyright (C) 2015-2016 Avencall
# SPDX-License-Identifier: GPL-3.0+

import unittest
from hamcrest import assert_that
from hamcrest import equal_to

from mock import Mock

from xivo_agid.handlers.agentfeatures import AgentFeatures


class TestAgentFeatures(unittest.TestCase):

    def setUp(self):
        self._agi = Mock()
        self._cursor = Mock()
        self._args = Mock()
        self.agent_features = AgentFeatures(self._agi, self._cursor, self._args)

    def test_that_extract_queue_call_options_keep_valid_option(self):
        queue_options = 'abwdeht'
        result = self.agent_features._extract_queue_call_options(queue_options)
        assert_that(result, equal_to('wht'))

    def test_that_extract_queue_call_options_does_not_keep_params_in_parentheses(self):
        queue_options = 'abcdefg(abHh)tij'
        result = self.agent_features._extract_queue_call_options(queue_options)
        assert_that(result, equal_to('ti'))
