# -*- coding: utf-8 -*-

# Copyright (C) 2012-2013 Avencall
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

import json
import logging
import socket
import time
import threading
import urllib2
from xivo.moresynchro import RWLock
from xivo_agid import agid
from xivo_agid.directory import directory
from xivo_dao import cti_displays_dao, cti_context_dao, cti_directories_dao

logger = logging.getLogger(__name__)

PHONEBOOK_URL = 'http://localhost/service/ipbx/json.php/private/pbx_services/phonebook'
UPDATE_ADDRESS = 'localhost'
UPDATE_PORT = 5042
FETCH_WS_RETRY_INTERVAL = 10

_update_thread = None
_displays_mgr = directory.DisplaysMgr()
_contexts_mgr = directory.ContextsMgr()
_directories_mgr = directory.DirectoriesMgr()
_rw_lock = RWLock()
# XXX the following names are imported in xivo_agid.directory submodules
_phonebook = {}
_cursor = None


def callerid_forphones(agi, cursor, args):
    cid_name = agi.env['agi_calleridname']
    cid_number = agi.env['agi_callerid']

    global _cursor
    _cursor = cursor
    try:
        caller_id_all = _resolve_incoming_caller_id(cid_name, cid_number, agi)
    finally:
        _cursor = None

    if caller_id_all:
        agi.set_callerid(caller_id_all)


def _resolve_incoming_caller_id(cid_name, cid_number, agi):
    logger.debug('Resolving caller ID: incoming caller ID=%s %s',
                 cid_name, cid_number)

    if cid_name == cid_number or cid_name == 'unknown':
        return _get_cid_directory_lookup(cid_number, agi)
    else:
        return None


def _get_cid_directory_lookup(cid_number, agi):
    if _rw_lock.acquire_read(5):
        try:
            context_obj = _contexts_mgr.contexts['*']
            lookup_result = context_obj.lookup_reverse(None, cid_number)
        finally:
            _rw_lock.release()
    else:
        logger.error('could not do callerid_forphones: lock acquisition failed')
        lookup_result = None

    if lookup_result:
        result = []
        for key, value in lookup_result.iteritems():
            result.append("%s: %s" % (key, value))

        result = ",".join(result)

        agi.set_variable("XIVO_REVERSE_LOOKUP", result)
        return '"%s" <%s>' % (lookup_result['db-reverse'], cid_number)
    else:
        agi.set_variable("XIVO_REVERSE_LOOKUP", '')
        return None


def setup_callerid_forphones(cursor):
    if _update_thread is None:
        update_socket = _create_update_socket()
        _start_update_thread(update_socket)
        update_socket.sendto('update-config', update_socket.getsockname())
        update_socket.sendto('update-phonebook', update_socket.getsockname())


def _convert_raw_phonebook_to_phonebook_dict(raw_phonebook):
    pblist = {}
    for pitem in raw_phonebook:
        pbitem = {}
        for i1, v1 in pitem.iteritems():
            if isinstance(v1, dict):
                for i2, v2 in v1.iteritems():
                    if isinstance(v2, dict):
                        for i3, v3 in v2.iteritems():
                            idx = '.'.join([i1, i2, i3])
                            pbitem[idx] = v3
                    else:
                        idx = '.'.join([i1, i2])
                        pbitem[idx] = v2
            else:
                pbitem[i1] = v1
        myid = pbitem.get('phonebook.id')
        pblist[myid] = pbitem
    return pblist


def _create_update_socket():
    update_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        update_socket.bind((UPDATE_ADDRESS, UPDATE_PORT))
    except Exception:
        update_socket.close()
        raise
    else:
        return update_socket


def _start_update_thread(update_socket):
    global _update_thread
    _update_thread = threading.Thread(target=_update_thread_loop,
                                      args=(update_socket,))
    _update_thread.daemon = True
    _update_thread.start()


def _update_thread_loop(update_socket):
    try:
        while True:
            data, _ = update_socket.recvfrom(1024)
            data = data.rstrip()
            logger.info('executing update command %r', data)
            try:
                if data == 'update-config':
                    _update_cti_config()
                elif data == 'update-phonebook':
                    _update_phonebook()
                else:
                    logger.warning('received unknown command: %r', data)
            except Exception as e:
                logger.error('exception during update: %s', e, exc_info=True)
    finally:
        update_socket.close()


def _update_cti_config():
    if _rw_lock.acquire_write():
        try:
            displays = cti_displays_dao.get_config()
            contexts = cti_context_dao.get_config()
            directories = cti_directories_dao.get_config()
            _displays_mgr.update(displays)
            _directories_mgr.update(directories)
            _contexts_mgr.update(_displays_mgr.displays,
                                 _directories_mgr.directories,
                                 contexts)
        finally:
            _rw_lock.release()
    else:
        logger.error('could not update callerid_forphones config: lock acquisition failed')


def _fetch_from_ws(url):
    while True:
        try:
            fobj = urllib2.urlopen(url, timeout=10)
        except urllib2.HTTPError:
            raise
        except urllib2.URLError as e:
            logger.warning('error while fetching url %s: %s', url, e)
            logger.warning('sleeping %s seconds before retrying', FETCH_WS_RETRY_INTERVAL)
            time.sleep(FETCH_WS_RETRY_INTERVAL)
        else:
            try:
                return json.load(fobj)
            finally:
                fobj.close()


def _update_phonebook():
    global _phonebook
    try:
        raw_phonebook = _fetch_from_ws(PHONEBOOK_URL)
        _phonebook = _convert_raw_phonebook_to_phonebook_dict(raw_phonebook)
    except ValueError:
        # empty phonebook
        _phonebook = {}


agid.register(callerid_forphones, setup_callerid_forphones)
