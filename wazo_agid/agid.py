# Copyright 2008-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import signal
import logging
import socketserver
import time

from threading import Lock
from typing import Callable

import psycopg2
from psycopg2.extras import DictCursor
from sqlalchemy.engine.url import make_url

from xivo import agitb
from xivo import moresynchro
from xivo_dao.helpers.db_utils import session_scope

from wazo_agid.fastagi import FastAGI, FastAGIDialPlanBreak

logger = logging.getLogger(__name__)

SetupFunction = Callable[[DictCursor], None]
HandleFunction = Callable[[FastAGI, DictCursor, list], None]

CONNECTION_TIMEOUT = 60

_server: AGID | None = None
_handlers: dict[str, Handler] = {}


def info_from_db_uri(db_uri: str) -> dict[str, str | int]:
    parsed_url = make_url(db_uri)
    exceptions = {'database': 'dbname', 'username': 'user'}
    return {
        exceptions.get(name, name): value
        for name, value in parsed_url.translate_connect_args().items()
    }


class DBConnectionPool:
    def __init__(self):
        self.conns: list[psycopg2.connection] = []
        self.size = 0
        self.connection_info: dict[str, str | int] = {}
        self.lock = Lock()

    def reload(self, size: int, db_uri: str):
        with self.lock:
            for conn in self.conns:
                conn.close()
            self.connection_info = info_from_db_uri(db_uri)
            self.conns = [psycopg2.connect(**self.connection_info) for _ in range(size)]
            self.size = size
        logger.debug("reloaded db conn pool")

    def acquire(self) -> psycopg2.connection:
        with self.lock:
            try:
                conn = self.conns.pop()
                logger.debug("acquiring connection: got connection from pool")
            except IndexError:
                conn = psycopg2.connect(**self.connection_info)
                logger.debug("acquiring connection: pool empty, created new connection")
        return conn

    def release(self, conn: psycopg2.connection):
        with self.lock:
            if len(self.conns) < self.size:
                self.conns.append(conn)
                logger.debug(
                    "releasing connection: pool not full, refilled with connection"
                )
            else:
                conn.close()
                logger.debug("releasing connection: pool full, connection closed")


class FastAGIRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            logger.debug("handling request")

            fagi = FastAGI(self.rfile, self.wfile, self.config)
            except_hook = agitb.Hook(agi=fagi)

            conn = self.server.db_conn_pool.acquire()
            try:
                cursor = conn.cursor(cursor_factory=DictCursor)

                handler_name = fagi.env['agi_network_script']
                logger.debug("delegating request handling %r", handler_name)

                try:
                    _handlers[handler_name].handle(fagi, cursor, fagi.args)
                    conn.commit()
                except psycopg2.DatabaseError:
                    logger.debug("Database error encountered. Rolling back.")
                    conn.rollback()
                    raise

                fagi.verbose(f'AGI handler {handler_name!r} successfully executed')
                logger.debug("request successfully handled")
            finally:
                self.server.db_conn_pool.release(conn)

        # Attempt to relay errors to Asterisk, but if it fails, we
        # just give up.
        # XXX It may be here that dropped database connection
        # exceptions could be caught.
        except FastAGIDialPlanBreak as message:
            logger.info("invalid request, dial plan broken")

            try:
                fagi.verbose(message)
                # TODO: see under
                fagi.appexec('Goto', 'agi_fail,s,1')
                fagi.fail()
            except Exception:
                pass
        except Exception:
            logger.exception("unexpected exception")
            try:
                except_hook.handle()
                # TODO: (important!)
                #   - rename agi_fail, or find a better way
                #   - move at the beginning of a safe block
                fagi.appexec('Goto', 'agi_fail,s,1')
                fagi.fail()
            except Exception:
                pass


class AGID(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    initialized = False
    request_queue_size = 20
    db_conn_pool: DBConnectionPool

    def __init__(self, config):
        logger.info('wazo-agid starting...')

        self.config = config
        signal.signal(signal.SIGHUP, sighup_handle)

        self.db_conn_pool = DBConnectionPool()
        self.setup()

        FastAGIRequestHandler.config = config
        socketserver.ThreadingTCPServer.__init__(
            self, (self.listen_addr, self.listen_port), FastAGIRequestHandler
        )

        self.initialized = True

    def setup(self):
        if not self.initialized:
            self.listen_addr = self.config["listen_address"]
            logger.debug("listen_addr: %s", self.listen_addr)

            self.listen_port = int(self.config["listen_port"])
            logger.debug("listen_port: %d", self.listen_port)

        conn_pool_size = int(self.config["connection_pool_size"])

        db_uri = self.config["db_uri"]

        for i in range(1, CONNECTION_TIMEOUT + 1):
            try:
                self.db_conn_pool.reload(conn_pool_size, db_uri)
                break
            except psycopg2.OperationalError:
                if i < CONNECTION_TIMEOUT:
                    time.sleep(1)
                    continue
                logger.error('Connecting to database timed out. Giving up.')
                raise


class Handler:
    def __init__(
        self,
        handler_name: str,
        setup_fn: SetupFunction | None,
        handle_fn: HandleFunction,
    ):
        self.handler_name = handler_name
        self.setup_fn = setup_fn
        self.handle_fn = handle_fn
        self.lock = moresynchro.RWLock()

    def setup(self, cursor: DictCursor):
        if self.setup_fn:
            self.setup_fn(cursor)

    def reload(self, cursor: DictCursor):
        if self.setup_fn:
            if not self.lock.acquire_write():
                logger.error("deadlock detected and avoided for %r", self.handler_name)
                logger.error("%r has not be reloaded", self.handler_name)
                return
            try:
                self.setup_fn(cursor)
                logger.debug('handler %r reloaded', self.handler_name)
            finally:
                self.lock.release()

    def handle(self, agi: FastAGI, cursor: DictCursor, args: list):
        self.lock.acquire_read()
        try:
            with session_scope():
                self.handle_fn(agi, cursor, args)
        finally:
            self.lock.release()


def register(handle_fn: HandleFunction, setup_fn: SetupFunction = None):
    handler_name = handle_fn.__name__

    if handler_name in _handlers:
        raise ValueError("handler %r already registered", handler_name)

    _handlers[handler_name] = Handler(handler_name, setup_fn, handle_fn)


def sighup_handle(signum, frame):
    logger.debug("reloading core engine")
    _server.setup()

    conn = _server.db_conn_pool.acquire()
    try:
        cursor = conn.cursor(cursor_factory=DictCursor)

        logger.debug("reloading handlers")
        for handler in _handlers.values():
            handler.reload(cursor)

        conn.commit()
        logger.debug("finished reload")
    finally:
        _server.db_conn_pool.release(conn)


def run():
    conn = _server.db_conn_pool.acquire()
    try:
        cursor = conn.cursor(cursor_factory=DictCursor)

        logger.debug("list of handlers: %s", ', '.join(sorted(_handlers)))

        for handler in _handlers.values():
            handler.setup(cursor)

        conn.commit()
    finally:
        _server.db_conn_pool.release(conn)

    _server.serve_forever()


def init(config):
    global _server
    _server = AGID(config)
