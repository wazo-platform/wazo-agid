# Copyright 2013-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_agid import dialplan_variables


class Handler:
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
