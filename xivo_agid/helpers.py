# -*- coding: utf-8 -*-

# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import time

from jinja2 import Template
from unidecode import unidecode


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
