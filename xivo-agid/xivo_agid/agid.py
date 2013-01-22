# -*- coding: utf-8 -*-

# Copyright (C) 2008-2013 Avencall
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

import signal
import logging
import SocketServer
import ConfigParser
from threading import Lock

from xivo import agitb
from xivo import anysql
from xivo import moresynchro

from xivo_agid import fastagi


AGI_CONFFILE = "/etc/pf-xivo/xivo-agid.conf"
LISTEN_ADDR_DEFAULT = "127.0.0.1"
LISTEN_PORT_DEFAULT = 4573
CONN_POOL_SIZE_DEFAULT = 10

log = logging.getLogger('xivo_agid.agid')

_server = None
_handlers = {}


class DBConnectionPool(object):
    def __init__(self):
        self.conns = []
        self.size = 0
        self.db_uri = None
        self.lock = Lock()

    def reload(self, size, db_uri):
        with self.lock:
            for conn in self.conns:
                conn.close()

            self.conns = [anysql.connect_by_uri(db_uri) for _ in xrange(size)]

            self.size = size
            self.db_uri = db_uri
        log.debug("reloaded db conn pool")

    def acquire(self):
        with self.lock:
            try:
                conn = self.conns.pop()
                log.debug("acquiring connection: got connection from pool")
            except IndexError:
                conn = anysql.connect_by_uri(self.db_uri)
                log.debug("acquiring connection: pool empty, created new connection")

        return conn

    def release(self, conn):
        with self.lock:
            if len(self.conns) < self.size:
                self.conns.append(conn)
                log.debug("releasing connection: pool not full, refilled with connection")
            else:
                conn.close()
                log.debug("releasing connection: pool full, connection closed")


class FastAGIRequestHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        try:
            log.debug("handling request")

            fagi = fastagi.FastAGI(self.rfile, self.wfile)
            except_hook = agitb.Hook(agi=fagi)

            conn = _server.db_conn_pool.acquire()
            try:
                cursor = conn.cursor()

                handler_name = fagi.env['agi_network_script']
                log.debug("delegating request handling %r", handler_name)
                _handlers[handler_name].handle(fagi, cursor, fagi.args)

                conn.commit()

                fagi.verbose('AGI handler %r successfully executed' % handler_name)
                log.debug("request successfully handled")
            finally:
                _server.db_conn_pool.release(conn)

        # Attempt to relay errors to Asterisk, but if it fails, we
        # just give up.
        # XXX It may be here that dropping database connection
        # exceptions could be catched.
        except fastagi.FastAGIDialPlanBreak, message:
            log.info("invalid request, dial plan broken")

            try:
                fagi.verbose(message)
                # TODO: see under
                fagi.appexec('Goto', 'agi_fail,s,1')
                fagi.fail()
            except Exception:
                pass
        except:
            log.exception("unexpected exception")

            try:
                except_hook.handle()
                # TODO: (important!)
                #   - rename agi_fail, or find a better way
                #   - move at the beginning of a safe block
                fagi.appexec('Goto', 'agi_fail,s,1')
                fagi.fail()
            except Exception:
                pass


class AGID(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True
    initialized = False

    def __init__(self):
        log.info('xivo-agid starting...')

        signal.signal(signal.SIGHUP, sighup_handle)

        self.db_conn_pool = DBConnectionPool()
        self.setup()

        SocketServer.ThreadingTCPServer.__init__(self,
                                                 (self.listen_addr, self.listen_port),
                                                 FastAGIRequestHandler)

        self.initialized = True

    def setup(self):
        config = ConfigParser.RawConfigParser()
        config.readfp(open(AGI_CONFFILE))

        if not self.initialized:
            try:
                self.listen_addr = config.get("general", "listen_addr")
            except ConfigParser.NoOptionError:
                self.listen_addr = LISTEN_ADDR_DEFAULT

            log.debug("listen_addr: %s", self.listen_addr)

            try:
                self.listen_port = config.getint("general", "listen_port")
            except ConfigParser.NoOptionError:
                self.listen_port = LISTEN_PORT_DEFAULT

            log.debug("listen_port: %d", self.listen_port)

        try:
            conn_pool_size = config.getint("general", "conn_pool_size")
        except ConfigParser.NoOptionError:
            conn_pool_size = CONN_POOL_SIZE_DEFAULT

        db_uri = config.get("db", "db_uri")
        self.db_conn_pool.reload(conn_pool_size, db_uri)


class Handler(object):
    def __init__(self, handler_name, setup_fn, handle_fn):
        self.handler_name = handler_name
        self.setup_fn = setup_fn
        self.handle_fn = handle_fn
        self.lock = moresynchro.RWLock()

    def setup(self, cursor):
        if self.setup_fn:
            self.setup_fn(cursor)

    def reload(self, cursor):
        if self.setup_fn:
            if not self.lock.acquire_write():
                log.error("deadlock detected and avoided for %r", self.handler_name)
                log.error("%r has not be reloaded", self.handler_name)
                return
            try:
                self.setup_fn(cursor)
                log.debug('handler %r reloaded', self.handler_name)
            finally:
                self.lock.release()

    def handle(self, agi, cursor, args):
        self.lock.acquire_read()
        try:
            self.handle_fn(agi, cursor, args)
        finally:
            self.lock.release()


def register(handle_fn, setup_fn=None):
    handler_name = handle_fn.__name__

    if handler_name in _handlers:
        raise ValueError("handler %r already registered", handler_name)

    _handlers[handler_name] = Handler(handler_name, setup_fn, handle_fn)


def sighup_handle(signum, frame):
    log.debug("reloading core engine")
    _server.setup()

    conn = _server.db_conn_pool.acquire()
    try:
        cursor = conn.cursor()

        log.debug("reloading handlers")
        for handler in _handlers.itervalues():
            handler.reload(cursor)

        conn.commit()
        log.debug("finished reload")
    finally:
        _server.db_conn_pool.release(conn)


def run():
    conn = _server.db_conn_pool.acquire()
    try:
        cursor = conn.cursor()

        log.debug("list of handlers: %s", ', '.join(sorted(_handlers.iterkeys())))

        for handler in _handlers.itervalues():
            handler.setup(cursor)

        conn.commit()
    finally:
        _server.db_conn_pool.release(conn)

    _server.serve_forever()


def init():
    global _server
    _server = AGID()
