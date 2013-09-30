# -*- coding: utf-8 -*-

# Copyright (C) 2009-2013 Avencall
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

from itertools import ifilter, imap
from xivo_dird.directory.data_sources.directory_data_source import DirectoryDataSource


class PhonebookDirectoryDataSource(DirectoryDataSource):
    def __init__(self, key_mapping):
        self._key_mapping = key_mapping
        self._map_fun = self._new_map_function()

    def lookup(self, string, fields, contexts=None):
        # XXX ugly
        from xivo_agid.modules.callerid_forphones import _phonebook
        filter_fun = self._new_filter_function(string, fields)
        return imap(self._map_fun, ifilter(filter_fun,
                                           _phonebook.itervalues()))

    def _new_filter_function(self, string, fields):
        lowered_string = string.lower()

        def aux(phonebook_entry):
            for field in fields:
                if field in phonebook_entry:
                    if lowered_string in phonebook_entry[field].lower():
                        return True
            return False
        return aux

    def _new_map_function(self):
        def aux(phonebook_entry):
            return dict((std_key, phonebook_entry[src_key]) for (std_key, src_key) in
                        self._key_mapping.iteritems() if
                        src_key in phonebook_entry)
        return aux

    @classmethod
    def new_from_contents(cls, contents):
        key_mapping = cls._get_key_mapping(contents)
        return cls(key_mapping)
