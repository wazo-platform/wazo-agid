# Copyright 2008-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import signal
import socketserver
import time
from collections.abc import Callable
from contextlib import contextmanager
from types import FrameType
from typing import Any

import psycopg2
from psycopg2.extras import DictCursor
from sqlalchemy.engine.url import URL, make_url
from xivo import agitb, moresynchro
from xivo_dao.helpers.db_utils import session_scope

from wazo_agid.fastagi import FastAGI, FastAGIDialPlanBreak

logger = logging.getLogger(__name__)

SetupFunction = Callable[[DictCursor], None]
HandleFunction = Callable[[FastAGI, DictCursor, list], None]

CONNECTION_TIMEOUT = 60

_server: AGID = None  # type: ignore[assignment]
_handlers: dict[str, Handler] = {}


def info_from_db_uri(db_uri: str) -> dict[str, str | int]:
    parsed_url: URL = make_url(db_uri)
    exceptions = {'database': 'dbname', 'username': 'user'}
    connect_args = {
        exceptions.get(name, name): value
        for name, value in parsed_url.translate_connect_args().items()
    }
    query_args = parsed_url.query
    return dict(query_args, **connect_args)


class Database:
    def __init__(self, db_uri: str):
        self.connection_info = info_from_db_uri(db_uri)

    @contextmanager
    def connection(self):
        with psycopg2.connect(**self.connection_info) as connection:
            yield connection

    @contextmanager
    def transaction(self, connection: psycopg2.connection) -> DictCursor:
        try:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                yield cursor
                connection.commit()
        except psycopg2.DatabaseError:
            logger.debug("Database error encountered. Rolling back.")
            connection.rollback()
            raise


class FastAGIRequestHandler(socketserver.StreamRequestHandler):
    config: dict[str, Any]

    def handle(self):
        try:
            logger.debug("handling request")

            fagi = FastAGI(self.rfile, self.wfile, self.config)
            except_hook = agitb.Hook(agi=fagi)

            handler_name = fagi.env['agi_network_script']
            logger.debug("delegating request handling %r", handler_name)
            with _server.database.connection() as conn:
                with _server.database.transaction(conn) as cursor:
                    _handlers[handler_name].handle(fagi, cursor, fagi.args)

                fagi.verbose(f'AGI handler {handler_name!r} successfully executed')
                logger.debug("request successfully handled")

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
    # Use Daemon threads to avoid memory leak
    # see bpo-37193 https://bugs.python.org/issue37193
    daemon_threads = True

    def __init__(self, config: dict[str, Any]) -> None:
        logger.info('wazo-agid starting...')

        self.config = config
        signal.signal(signal.SIGHUP, sighup_handle)

        self.database = Database(self.config["db_uri"])
        self.setup()

        FastAGIRequestHandler.config = config
        socketserver.ThreadingTCPServer.__init__(
            self, (self.listen_addr, self.listen_port), FastAGIRequestHandler
        )

        self.initialized = True

    def setup(self) -> None:
        if not self.initialized:
            self.listen_addr = self.config["listen_address"]
            logger.debug("listen_addr: %s", self.listen_addr)

            self.listen_port = int(self.config["listen_port"])
            logger.debug("listen_port: %d", self.listen_port)

        for i in range(1, CONNECTION_TIMEOUT + 1):
            try:
                with self.database.connection():
                    pass
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
    ) -> None:
        self.handler_name = handler_name
        self.setup_fn = setup_fn
        self.handle_fn = handle_fn
        self.lock = moresynchro.RWLock()

    def setup(self, cursor: DictCursor) -> None:
        if self.setup_fn:
            self.setup_fn(cursor)

    def reload(self, cursor: DictCursor) -> None:
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

    def handle(self, agi: FastAGI, cursor: DictCursor, args: list[str]):
        self.lock.acquire_read()
        try:
            with session_scope():
                self.handle_fn(agi, cursor, args)
        finally:
            self.lock.release()


def register(handle_fn: HandleFunction, setup_fn: SetupFunction | None = None) -> None:
    handler_name = handle_fn.__name__

    if handler_name in _handlers:
        raise ValueError("handler %r already registered", handler_name)

    _handlers[handler_name] = Handler(handler_name, setup_fn, handle_fn)


def sighup_handle(signum: int, frame: FrameType | None) -> None:
    logger.debug("reloading core engine")
    _server.setup()

    logger.debug("reloading handlers")
    with _server.database.connection() as conn:
        with _server.database.transaction(conn) as cursor:
            for handler in _handlers.values():
                handler.reload(cursor)
            logger.debug("finished reload")


def run() -> None:
    logger.debug("list of handlers: %s", ', '.join(sorted(_handlers)))
    with _server.database.connection() as conn:
        with _server.database.transaction(conn) as cursor:
            for handler in _handlers.values():
                handler.setup(cursor)

    _server.serve_forever()


def init(config) -> None:
    global _server
    _server = AGID(config)
