# -*- coding: utf-8 -*-

# Copyright (C) 2013-2014 Avencall
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

from xivo_agid import dialplan_variables


class Handler(object):
    def __init__(self, agi, cursor, args):
        self._agi = agi
        self._cursor = cursor
        self._args = args

    def _set_path(self, path_type, path_id):
        # schedule path
        path = self._agi.get_variable(dialplan_variables.PATH)
        if path is None or len(path) == 0:
            self._agi.set_variable(dialplan_variables.PATH, path_type)
            self._agi.set_variable(dialplan_variables.PATH_ID, path_id)
