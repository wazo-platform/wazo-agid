# -*- coding: utf-8 -*-

# Copyright (C) 2013 Avencall
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

import re as _re
import os as _os


def _package_path():
    return _os.path.dirname(_os.path.abspath(__file__))


def _is_package_child(path, name):
    full = _os.path.join(path, name)
    if _os.path.isdir(full):
        for sub in _os.listdir(full):
            if _re.match(r"__init__\.py[a-z]?$", sub):
                return True
        else:
            return False
    else:
        return _re.search(r"\.py[a-z]*$", name) \
            and '__init__' not in name


# Python doesn't really want us to do that because of
# compatibility with stupid operating systems, but thanks
# to this function we can do it anyway... :)
def _get_module_list(path):
    return list(set([_re.sub(r"\.py[a-z]?$", "", name)
                     for name in _os.listdir(path)
                     if _is_package_child(path, name)]))

__all__ = _get_module_list(_package_path())
