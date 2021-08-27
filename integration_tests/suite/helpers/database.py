# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import sqlalchemy as sa

from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from xivo_dao.tests.test_dao import ItemInserter

logger = logging.getLogger(__name__)

# This tenant_uuid is populated into the test database
TENANT_UUID = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1'


class DbHelper(object):

    TEMPLATE = "xivotemplate"

    @classmethod
    def build(cls, user, password, host, port, db):
        tpl = "postgresql://{user}:{password}@{host}:{port}"
        uri = tpl.format(user=user, password=password, host=host, port=port)
        return cls(uri, db)

    def __init__(self, uri, db):
        self.uri = uri
        self.db = db
        self._engine = self.create_engine()

    def is_up(self):
        try:
            self.connect()
            return True
        except Exception as e:
            logger.debug('Database is down: %s', e)
            return False

    def create_engine(self, db=None, isolate=False):
        db = db or self.db
        uri = "{}/{}".format(self.uri, db)
        if isolate:
            return sa.create_engine(uri, isolation_level='AUTOCOMMIT')
        return sa.create_engine(uri)

    def connect(self):
        return self._engine.connect()

    def recreate(self):
        engine = self.create_engine("postgres", isolate=True)
        connection = engine.connect()
        connection.execute(
            """
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db}'
            AND pid <> pg_backend_pid()
            """.format(
                db=self.db
            )
        )
        connection.execute("DROP DATABASE IF EXISTS {db}".format(db=self.db))
        connection.execute(
            "CREATE DATABASE {db} TEMPLATE {template}".format(
                db=self.db, template=self.TEMPLATE
            )
        )
        connection.close()

    def execute(self, query, **kwargs):
        with self.connect() as connection:
            connection.execute(text(query), **kwargs)

    @contextmanager
    def queries(self):
        with self.connect() as connection:
            yield DatabaseQueries(connection)


class DatabaseQueries(object):
    def __init__(self, connection):
        self.connection = connection
        self.Session = sessionmaker(bind=connection)

    @contextmanager
    def inserter(self):
        session = self.Session()
        yield ItemInserter(session, tenant_uuid=TENANT_UUID)
        session.commit()

    def insert_user_line_extension(self, **kwargs):
        with self.inserter() as inserter:
            ule = inserter.add_user_line_with_exten(**kwargs)
            user = {
                'id': ule.user.id,
                'uuid': ule.user.uuid,
                'tenant_uuid': ule.user.tenant_uuid,
                'simultcalls': ule.user.simultcalls,
                'ringseconds': ule.user.ringseconds,
                'enablednd': ule.user.enablednd,
                'enablevoicemail': ule.user.enablevoicemail,
                'enableunc': ule.user.enableunc,
                'musiconhold': ule.user.musiconhold,
            }
            line = {
                'id': ule.line.id,
                'name': ule.line.name,
            }
            extension = {
                'id': ule.extension.id,
                'exten': ule.extension.exten,
                'context': ule.extension.context,
            }
            return user, line, extension

    def insert_endpoint_sip(self, **kwargs):
        with self.inserter() as inserter:
            sip = inserter.add_endpoint_sip(**kwargs)
            return {'uuid': sip.uuid}

    def insert_agent(self, **kwargs):
        with self.inserter() as inserter:
            agent = inserter.add_agent(**kwargs)
            return {
                'id': agent.id,
                'tenant_uuid': agent.tenant_uuid,
                'number': agent.number,
                'language': agent.language,
            }

    def insert_extension(self, **kwargs):
        with self.inserter() as inserter:
            extension = inserter.add_extension(**kwargs)
            return {
                'exten': extension.exten,
                'context': extension.context,
            }

    def insert_switchboard(self, **kwargs):
        with self.inserter() as inserter:
            switchboard = inserter.add_switchboard(**kwargs)
            return {
                'uuid': switchboard.uuid,
            }
