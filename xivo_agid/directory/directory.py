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
from itertools import chain, imap
from operator import itemgetter

from xivo_dird.directory.data_sources.csv_file_directory_data_source import CSVFileDirectoryDataSource
from xivo_dird.directory.data_sources.http import HTTPDirectoryDataSource
from xivo_agid.directory.data_sources.internal import InternalDirectoryDataSource
from xivo_dird.directory.data_sources.ldap import LDAPDirectoryDataSource
from xivo_agid.directory.data_sources.phonebook import PhonebookDirectoryDataSource

logger = logging.getLogger('directories')

SPACE_DASH = re.compile('[ -]')


class Context(object):
    def __init__(self, directories, display, didextens):
        """
        directories -- a list of directory objects to use for direct lookup
        display -- a display object to format the results of direct lookup
        didextens -- a dictionary mapping extension number to list of
          directory objects for reverse lookup
        """
        self._directories = directories
        self._display = display
        self._didextens = didextens

    def lookup_direct(self, string, contexts=None):
        """Return a tuple (<headers>, <resultlist>)."""
        if self._display is None:
            raise Exception('No display defined for this context')
        directory_results = []
        for directory in self._directories:
            try:
                directory_result = directory.lookup_direct(string, contexts)
            except Exception:
                logger.error('Error while looking up in directory %s for %s',
                             directory.name, string, exc_info=True)
            else:
                directory_results.append(directory_result)
        combined_results = chain.from_iterable(directory_results)
        resultlist = list(self._display.format(combined_results))
        return self._display.display_header, resultlist

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
    def new_from_contents(cls, avail_displays, avail_directories, contents):
        """Return a new instance of this class from "configuration contents"
        and dictionaries of displays and directories object.
        """
        directories = cls._directories_from_contents(avail_directories, contents)
        display = cls._display_from_contents(avail_displays, contents)
        didextens = cls._didextens_from_contents(avail_directories, contents)
        return cls(directories, display, didextens)

    @classmethod
    def _directories_from_contents(cls, avail_directories, contents):
        directory_ids = contents.get('directories', [])
        return cls._new_directory_list(directory_ids, avail_directories)

    @staticmethod
    def _display_from_contents(avail_displays, contents):
        display_id = contents.get('display')
        return avail_displays.get(display_id)

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


_APPLY_SUBS_REGEX = re.compile(r'\{([^}]+)\}')


def _apply_subs(display_elem, result):
    fmt_string = display_elem['fmt']
    # use of 1-element list since we can't rebind local variables in inner scope
    # in python2
    nb_subs = [0]
    nb_succesfull_subs = [0]

    def aux(m):
        nb_subs[0] += 1
        var_name = m.group(1)
        if var_name in result:
            nb_succesfull_subs[0] += 1
            return result[var_name]
        else:
            return m.group()
    fmted_string = _APPLY_SUBS_REGEX.sub(aux, fmt_string)
    # use default value if there was at least one substitution tried
    # but none were successful
    if nb_subs[0] > 0 and nb_succesfull_subs[0] == 0:
        fmted_string = display_elem.get('default', '')
    return fmted_string


class Display(object):
    def __init__(self, display_elems):
        """
        display_elems -- a list of dictionaries with the followings keys:
          'title', 'default' and 'fmt'.
        """
        self._display_elems = display_elems
        self.display_header = [e['title'] for e in display_elems]
        self._map_fun = self._new_map_function()

    def format(self, results):
        """Return an iterator over the formated results."""
        return imap(self._map_fun, results)

    def _new_map_function(self):
        def aux(result):
            return ';'.join(_apply_subs(display_elem, result) for
                            display_elem in self._display_elems)
        return aux

    @classmethod
    def new_from_contents(cls, contents):
        contents = list({'title': v[0], 'default': v[2], 'fmt': v[3]} for
                        (_, v) in
                        sorted(contents.iteritems(), key=itemgetter(0)))
        return cls(contents)


class DirectoryAdapter(object):
    """Adapt a DirectoryDataSource instance to the Directory interface,
    i.e. to something with a name attribute, a lookup_direct and
    lookup_reverse method, etc...
    """
    def __init__(self, directory_src, name, match_direct, match_reverse):
        self._directory_src = directory_src
        self.name = name
        self._match_direct = match_direct
        self._match_reverse = match_reverse
        self._map_fun = self._new_map_function()

    def _new_map_function(self):
        def aux(result):
            result['xivo-directory'] = self.name
            return result
        return aux

    def lookup_direct(self, string, contexts=None):
        return imap(self._map_fun, self._directory_src.lookup(string, self._match_direct, contexts))

    def lookup_reverse(self, string):
        return self._directory_src.lookup(string, self._match_reverse)

    @classmethod
    def new_from_contents(cls, directory, contents):
        name = contents['name']
        match_direct = contents['match_direct']
        match_reverse = contents['match_reverse']
        return cls(directory, name, match_direct, match_reverse)


class ContextsMgr(object):
    def __init__(self):
        self.contexts = {}

    def update(self, avail_displays, avail_directories, contents):
        self.contexts = {}
        for context_id, context_contents in contents.iteritems():
            try:
                self.contexts[context_id] = Context.new_from_contents(
                    avail_displays, avail_directories, context_contents)
            except Exception:
                logger.error('Error while creating context %s from %s',
                             context_id, context_contents, exc_info=True)


class DisplaysMgr(object):
    def __init__(self):
        self.displays = {}
        self._old_contents = {}

    def update(self, contents):
        # remove old displays
        # deleting a key will raise a RuntimeError if you do not use .keys() here
        for display_id in self.displays.keys():
            if display_id not in contents:
                del self.displays[display_id]
        # add/update displays
        for display_id, display_contents in contents.iteritems():
            if display_contents != self._old_contents.get(display_id):
                try:
                    self.displays[display_id] = Display.new_from_contents(display_contents)
                except Exception:
                    logger.error('Error while creating display %s from %s',
                                 display_id, display_contents, exc_info=True)
        self._old_contents = contents


class DirectoriesMgr(object):
    _DIRECTORY_SRC_CLASSES = {
        'file': CSVFileDirectoryDataSource,
        'http': HTTPDirectoryDataSource,
        'internal': InternalDirectoryDataSource,
        'ldapfilter': LDAPDirectoryDataSource,
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
                try:
                    class_ = self._get_directory_class(directory_contents)
                    directory_src = class_.new_from_contents(directory_contents)
                    directory = DirectoryAdapter.new_from_contents(directory_src, directory_contents)
                    self.directories[directory_id] = directory
                except Exception:
                    logger.error('Error while creating directory %s from %s',
                                 directory_id, directory_contents, exc_info=True)
        self._old_contents = contents

    def _get_directory_class(self, directory_contents):
        uri = directory_contents['uri']
        kind = uri.split(':', 1)[0]
        return self._DIRECTORY_SRC_CLASSES[kind]
