# -*- coding: utf-8 -*-
# Copyright 2017-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from hamcrest import (
    assert_that,
    equal_to,
    greater_than,
)
from mock import Mock

from ..helpers import (
    CallRecordingNameGenerator,
    is_registered_and_mobile,
)


class TestIsRegisteredAndMobile(unittest.TestCase):

    def test_no_registered_contacts(self):
        agi = Mock()
        agi.get_variable.return_value = ''

        result = is_registered_and_mobile(agi, 'name')

        assert_that(result, equal_to(False))

    def test_one_contact_not_mobile(self):
        def get_variable(key):
            variables = {
                'PJSIP_AOR(name,contact)': 'the-contact',
            }
            return variables.get(key, '')

        agi = Mock()
        agi.get_variable.side_effect = get_variable

        result = is_registered_and_mobile(agi, 'name')

        assert_that(result, equal_to(False))

    def test_multiple_contacts_no_mobile(self):
        def get_variable(key):
            variables = {
                'PJSIP_AOR(name,contact)': 'contact;1,contact;2,contact;3',
            }
            return variables.get(key, '')

        agi = Mock()
        agi.get_variable.side_effect = get_variable

        result = is_registered_and_mobile(agi, 'name')

        assert_that(result, equal_to(False))

    def test_multiple_contacts_one_mobile(self):
        def get_variable(key):
            variables = {
                'PJSIP_AOR(name,contact)': 'contact;1,contact;2,contact;3',
                'PJSIP_CONTACT(contact;2,mobility)': 'mobile',
            }
            return variables.get(key, '')

        agi = Mock()
        agi.get_variable.side_effect = get_variable

        result = is_registered_and_mobile(agi, 'name')

        assert_that(result, equal_to(True))


class TestCallRecordingNameGenerator(unittest.TestCase):

    def test_that_unicode_chars_are_replaced(self):
        generator = CallRecordingNameGenerator(u'{{ name }}', 'wav')

        result = generator.generate(name=u'pépé')

        assert_that(result, equal_to('pepe.wav'))

    def test_that_unacceptable_chars_are_removed(self):
        generator = CallRecordingNameGenerator(u'{{ name }}', 'wav')

        result = generator.generate(name=u'test\**test')

        assert_that(result, equal_to('testtest.wav'))

    def test_that_empty_names_are_not_generated(self):
        generator = CallRecordingNameGenerator(u'{{ name }}', 'wav')

        result = generator.generate(name=u'\**')

        name, extension = result.rsplit('.', 1)
        assert_that(len(name), greater_than(0), 'a name should have been generated')
        assert_that(extension, equal_to('wav'))
