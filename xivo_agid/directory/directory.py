# -*- coding: utf-8 -*-

# Copyright (C) 2009-2015 Avencall
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

import logging
import re

from xivo_dird.directory.data_sources.csv_file_directory_data_source import CSVFileDirectoryDataSource
from xivo_dird.directory.data_sources.http import HTTPDirectoryDataSource
from xivo_dird.directory.data_sources.ldap import LDAPDirectoryDataSource
from xivo_agid.directory.data_sources.phonebook import PhonebookDirectoryDataSource

logger = logging.getLogger('directories')

SPACE_DASH = re.compile('[ -]')


class Context(object):

    def __init__(self, directories, didextens):
        """
        directories -- a list of directory objects to use for direct lookup
        didextens -- a dictionary mapping extension number to list of
          directory objects for reverse lookup
        """
        self._directories = directories
        self._didextens = didextens

    def lookup_reverse(self, did_number, number):
        """Return a list of directory entries."""
        if did_number in self._didextens:
            directories = self._didextens[did_number]
        elif '*' in self._didextens:
            directories = self._didextens['*']
        else:
            logger.warning('No directories for DID %s', did_number)

        for directory in directories:
            try:
                results = directory.lookup_reverse(number)
                for result in results:
                    for res in result.itervalues():
                        if SPACE_DASH.sub('', res) == number:
                            logger.info("lookup_reverse result : %s", result)
                            return result
            except Exception:
                logger.error('Error while looking up in directory %s for %s',
                             directory.name, number, exc_info=True)

        return {}

    @classmethod
    def new_from_contents(cls, avail_directories, contents):
        """Return a new instance of this class from "configuration contents"
        and dictionaries of displays and directories object.
        """
        directories = cls._directories_from_contents(avail_directories, contents)
        didextens = cls._didextens_from_contents(avail_directories, contents)
        return cls(directories, didextens)

    @classmethod
    def _directories_from_contents(cls, avail_directories, contents):
        directory_ids = contents.get('directories', [])
        return cls._new_directory_list(directory_ids, avail_directories)

    @classmethod
    def _didextens_from_contents(cls, avail_directories, contents):
        raw_didextens = contents.get('didextens', {})
        didextens = {}
        for exten, directory_ids in raw_didextens.iteritems():
            didextens[exten] = cls._new_directory_list(directory_ids, avail_directories)
        return didextens

    @staticmethod
    def _new_directory_list(directory_ids, avail_directories):
        directories = []
        for directory_id in directory_ids:
            try:
                directories.append(avail_directories[directory_id])
            except KeyError:
                logger.error('not using directory %r because not available', directory_id)
        return directories


class DirectoryAdapter(object):
    """Adapt a DirectoryDataSource instance to the Directory interface,
    i.e. to something with a name attribute, a lookup_reverse method, etc...
    """
    def __init__(self, directory_src, name, match_reverse):
        self._directory_src = directory_src
        self.name = name
        self._match_reverse = match_reverse
        self._map_fun = self._new_map_function()

    def _new_map_function(self):
        def aux(result):
            result['xivo-directory'] = self.name
            return result
        return aux

    def lookup_reverse(self, string):
        return self._directory_src.lookup(string, self._match_reverse)

    @classmethod
    def new_from_contents(cls, directory, contents):
        name = contents['name']
        match_reverse = contents['match_reverse']
        return cls(directory, name, match_reverse)


class ContextsMgr(object):
    def __init__(self):
        self.contexts = {}

    def update(self, avail_directories, contents):
        self.contexts = {}
        for context_id, context_contents in contents.iteritems():
            try:
                self.contexts[context_id] = Context.new_from_contents(
                    avail_directories, context_contents)
            except Exception:
                logger.error('Error while creating context %s from %s',
                             context_id, context_contents, exc_info=True)


class DirectoriesMgr(object):
    _DIRECTORY_SRC_CLASSES = {
        'csv': CSVFileDirectoryDataSource,
        'csv_ws': HTTPDirectoryDataSource,
        'ldap': LDAPDirectoryDataSource,
        'phonebook': PhonebookDirectoryDataSource,
    }

    def __init__(self):
        self.directories = {}
        self._old_contents = {}

    def update(self, contents):
        # remove old directories
        # deleting a key will raise a RuntimeError if you do not use .keys() here
        for directory_id in self.directories.keys():
            if directory_id not in contents:
                del self.directories[directory_id]
        # add/update directories
        for directory_id, directory_contents in contents.iteritems():
            if directory_contents != self._old_contents.get(directory_id):
                class_ = self._DIRECTORY_SRC_CLASSES.get(directory_contents['type'])
                if not class_:
                    continue
                try:
                    directory_src = class_.new_from_contents(directory_contents)
                    directory = DirectoryAdapter.new_from_contents(directory_src, directory_contents)
                    self.directories[directory_id] = directory
                except Exception:
                    logger.error('Error while creating directory %s from %s',
                                 directory_id, directory_contents, exc_info=True)
        self._old_contents = contents
