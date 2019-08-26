# -*- coding: utf-8 -*-
# Copyright 2017-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import time

from jinja2 import Template
from unidecode import unidecode


def is_webrtc(agi, protocol, name):
    if protocol != 'PJSIP':
        return False

    return agi.get_variable('PJSIP_ENDPOINT({},webrtc)'.format(name)) == 'yes'


def is_registered_and_mobile(agi, aor_name):
    raw_contacts = agi.get_variable('PJSIP_AOR({},contact)'.format(aor_name))
    if not raw_contacts:
        return False

    for contact in raw_contacts.split(','):
        mobility = agi.get_variable('PJSIP_CONTACT({},mobility)'.format(contact))
        if mobility == 'mobile':
            return True

    return False


class CallRecordingNameGenerator(object):

    valid_special_characters = ['/', '-', '_', ' ']

    def __init__(self, filename_template, filename_extension):
        self._template = Template(filename_template)
        self._extension = filename_extension

    def generate(self, context):
        generated_filename = self._template.render(context)
        ascii_filename = unidecode(generated_filename)
        filename = ''.join(c for c in ascii_filename if self._is_valid_character(c))
        if not filename:
            filename = str(time.time())

        return '.'.join([filename, self._extension])

    def _is_valid_character(self, c):
        return c.isalnum() or c in self.valid_special_characters
