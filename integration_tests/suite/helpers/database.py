# Copyright 2021-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import random
import uuid
from contextlib import contextmanager

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from xivo_dao.alchemy.all import (
    Extension,
    LineFeatures,
    OutcallTrunk,
    RightCallExten,
    UserFeatures,
)
from xivo_dao.tests.test_dao import ItemInserter

from .constants import TENANT_UUID

logger = logging.getLogger(__name__)


class DbHelper:
    TEMPLATE = "wazotemplate"

    @classmethod
    def build(cls, user, password, host, port, db):
        return cls(f'postgresql://{user}:{password}@{host}:{port}', db)

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
        uri = f'{self.uri}/{db}'
        if isolate:
            return sa.create_engine(uri, isolation_level='AUTOCOMMIT')
        return sa.create_engine(uri)

    def connect(self):
        return self._engine.connect()

    def recreate(self):
        engine = self.create_engine("postgres", isolate=True)
        connection = engine.connect()
        connection.execute(
            f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{self.db}'
            AND pid <> pg_backend_pid()
            """
        )
        connection.execute(f'DROP DATABASE IF EXISTS {self.db}')
        connection.execute(f'CREATE DATABASE {self.db} TEMPLATE {self.TEMPLATE}')
        connection.close()

    def execute(self, query, **kwargs):
        with self.connect() as connection:
            connection.execute(text(query), **kwargs)

    @contextmanager
    def queries(self):
        with self.connect() as connection:
            yield DatabaseQueries(connection)


class DatabaseQueries:
    def __init__(self, connection):
        self.connection = connection
        self.Session = sessionmaker(bind=connection)

    @contextmanager
    def inserter(self):
        session = self.Session()
        yield ItemInserter(session, tenant_uuid=TENANT_UUID)
        session.commit()

    def insert_tenant(self, **kwargs):
        with self.inserter() as inserter:
            tenant = inserter.add_tenant(
                uuid=kwargs.pop('uuid', str(uuid.uuid4())),
                **kwargs,
            )
            return {
                'uuid': tenant.uuid,
                'country': tenant.country
            }

    def insert_conference(self, **kwargs):
        with self.inserter() as inserter:
            conference = inserter.add_conference(**kwargs)
            return {
                'id': conference.id,
                'name': conference.name,
                'tenant_uuid': conference.tenant_uuid,
            }

    def insert_context(self, **kwargs):
        with self.inserter() as inserter:
            context = inserter.add_context(**kwargs)
            return {
                'name': context.name,
                'tenant_uuid': context.tenant_uuid,
            }

    def insert_user_line_extension(
        self, **kwargs
    ) -> tuple[UserFeatures, LineFeatures, Extension]:
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
            if ule.user.voicemail_id and kwargs.get('enablevoicemail'):
                ule.user.enablevoicemail = 1
                inserter.link_user_and_voicemail(ule.user, ule.user.voicemailid)
            return user, line, extension

    def insert_line(self, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = ''.join(
                random.choice('0123456789ABCDEF') for _ in range(6)
            )

        dao_kwargs = {
            'name': kwargs['name'],
            'device': kwargs.get('device', 1),
            'commented': kwargs.get('commented_line', 0),
        }
        if 'endpoint_sip_uuid' in kwargs:
            dao_kwargs['endpoint_sip_uuid'] = kwargs['endpoint_sip_uuid']
        if 'endpoint_sccp_uuid' in kwargs:
            dao_kwargs['endpoint_sccp_uuid'] = kwargs['endpoint_sccp_uuid']
        if 'endpoint_custom_uuid' in kwargs:
            dao_kwargs['endpoint_custom_uuid'] = kwargs['endpoint_custom_uuid']
        if 'context' in kwargs:
            dao_kwargs['context'] = kwargs['context']

        with self.inserter() as inserter:
            line = inserter.add_line(**dao_kwargs)
            return {'id': line.id, 'name': line.name}

    def insert_user_line(self, user_id, line_id, **kwargs):
        with self.inserter() as inserter:
            inserter.add_user_line(line_id=line_id, user_id=user_id, **kwargs)
            return {}

    def insert_extension_line(self, extension_id, line_id, **kwargs):
        with self.inserter() as inserter:
            inserter.add_line_extension(
                line_id=line_id, extension_id=extension_id, **kwargs
            )
            return {}

    def insert_call_permission(self, **kwargs):
        with self.inserter() as inserter:
            call_permission = inserter.add_call_permission(**kwargs)
            return {'id': call_permission.id, 'name': call_permission.name}

    def insert_call_extension_permission(self, **kwargs):
        with self.inserter() as inserter:
            call_extension_permission = RightCallExten(**kwargs)
            inserter.add_me(call_extension_permission)
            return {'id': call_extension_permission.id}

    def insert_user_call_permission(self, **kwargs):
        with self.inserter() as inserter:
            user_call_permission = inserter.add_user_call_permission(**kwargs)
            return {'id': user_call_permission.id}

    def insert_endpoint_sip(self, **kwargs):
        with self.inserter() as inserter:
            sip = inserter.add_endpoint_sip(**kwargs)
            return {'uuid': sip.uuid, 'name': sip.name}

    def insert_agent(self, **kwargs):
        with self.inserter() as inserter:
            agent = inserter.add_agent(**kwargs)
            return {
                'id': agent.id,
                'tenant_uuid': agent.tenant_uuid,
                'number': agent.number,
                'language': agent.language,
            }

    def insert_agent_login_status(self, **kwargs):
        with self.inserter() as inserter:
            inserter.add_agent_login_status(**kwargs)
            return {}

    def insert_queue(self, **kwargs):
        with self.inserter() as inserter:
            queue_kwargs = kwargs.pop('queue_kwargs', None)
            if queue_kwargs:
                if 'name' in kwargs:
                    queue_kwargs['name'] = kwargs['name']
                queue_kwargs.setdefault('category', 'queue')
                queue = inserter.add_queue(**queue_kwargs)
                kwargs['_queue'] = queue
                kwargs.setdefault('name', queue.name)
            queue_feature = inserter.add_queuefeatures(**kwargs)
            return {
                'id': queue_feature.id,
                'name': queue_feature.name,
                'context': queue_feature.context,
                'number': queue_feature.number,
                'url': queue_feature.url,
                'tenant_uuid': queue_feature.tenant_uuid,
            }

    def insert_extension(self, **kwargs):
        with self.inserter() as inserter:
            extension = inserter.add_extension(**kwargs)
            return {
                'id': extension.id,
                'exten': extension.exten,
                'context': extension.context,
            }

    def insert_feature_extension(self, **kwargs):
        with self.inserter() as inserter:
            extension = inserter.add_feature_extension(**kwargs)
            return {
                'uuid': extension.uuid,
                'exten': extension.exten,
                'feature': extension.feature,
            }

    def insert_meeting(self, **kwargs):
        with self.inserter() as inserter:
            meeting = inserter.add_meeting(**kwargs)
            return {
                'uuid': str(meeting.uuid),
                'name': meeting.name,
                'tenant_uuid': str(meeting.tenant_uuid),
                'number': meeting.number,
            }

    def insert_switchboard(self, **kwargs):
        with self.inserter() as inserter:
            switchboard = inserter.add_switchboard(**kwargs)
            return {
                'uuid': switchboard.uuid,
            }

    def insert_user(self, **kwargs):
        with self.inserter() as inserter:
            user = inserter.add_user(
                firstname=kwargs.get('firstname', 'unittest'),
                lastname=kwargs.get('lastname', 'unittest'),
                callerid=kwargs.get('callerid', '"unittest" <1234>'),
                musiconhold=kwargs.get('musiconhold', 'default'),
                enablednd=int(kwargs.pop('enablednd', False)),
                **kwargs,
            )
            return {
                'id': user.id,
                'uuid': user.uuid,
                'tenant_uuid': user.tenant_uuid,
                'enablednd': user.enablednd,
            }

    def insert_voicemail(self, **kwargs):
        with self.inserter() as inserter:
            voicemail = inserter.add_voicemail(**kwargs)
            return {
                'id': voicemail.id,
                'mailbox': voicemail.mailbox,
                'context': voicemail.context,
            }

    def insert_paging(self, **kwargs):
        with self.inserter() as inserter:
            if 'number' not in kwargs:
                kwargs['number'] = inserter._generate_paging_number()
            paging = inserter.add_paging(**kwargs)
            return {
                'id': paging.id,
                'number': paging.number,
                'tenant_uuid': paging.tenant_uuid,
            }

    def insert_paging_user(self, **kwargs):
        with self.inserter() as inserter:
            paging_user = inserter.add_paging_user(**kwargs)
            return {'caller': paging_user.caller}

    def insert_schedule(self, **kwargs):
        kwargs.setdefault('timezone', 'America/Montreal')
        with self.inserter() as inserter:
            schedule = inserter.add_schedule(**kwargs)
            return {
                'id': schedule.id,
                'name': schedule.name,
            }

    def insert_schedule_path(self, **kwargs):
        with self.inserter() as inserter:
            schedule_path = inserter.add_schedule_path(**kwargs)
            return {
                'schedule_id': schedule_path.schedule_id,
                'path': schedule_path.path,
                'path_id': schedule_path.pathid,
            }

    def insert_schedule_time(self, **kwargs):
        kwargs.setdefault('mode', 'open')
        kwargs.setdefault('hours', '00:00-23:59')
        kwargs.setdefault('weekdays', '1-7')
        kwargs.setdefault('monthdays', '1-31')
        kwargs.setdefault('months', '1-12')
        with self.inserter() as inserter:
            schedule_time = inserter.add_schedule_time(**kwargs)
            return {
                'id': schedule_time.id,
                'mode': schedule_time.mode,
                'schedule_id': schedule_time.schedule_id,
            }

    def insert_queue_skill_rule(self, **kwargs):
        with self.inserter() as inserter:
            skill_rule = inserter.add_queue_skill_rule(**kwargs)
            return {
                'id': skill_rule.id,
                'name': skill_rule.name,
                'rule': skill_rule.rule,
                'tenant_uuid': skill_rule.tenant_uuid,
            }

    def insert_incoming_call(self, **kwargs):
        with self.inserter() as inserter:
            incoming_call = inserter.add_incall(**kwargs)
            return {'id': incoming_call.id, 'tenant_uuid': incoming_call.tenant_uuid}

    def insert_outgoing_call(self, **kwargs):
        with self.inserter() as inserter:
            outgoing_call = inserter.add_outcall(**kwargs)
            return {'id': outgoing_call.id, 'tenant_uuid': outgoing_call.tenant_uuid}

    def insert_dial_pattern(self, **kwargs):
        with self.inserter() as inserter:
            dial_pattern = inserter.add_dialpattern(**kwargs)
            return {'id': dial_pattern.id}

    def insert_pickup(self, **kwargs):
        with self.inserter() as inserter:
            pickup = inserter.add_pickup(**kwargs)
            return {'id': pickup.id}

    def insert_pickup_member(self, **kwargs):
        with self.inserter() as inserter:
            inserter.add_pickup_member(**kwargs)
            return {}

    def insert_trunk(self, **kwargs):
        with self.inserter() as inserter:
            trunk = inserter.add_trunk(**kwargs)
            return {'id': trunk.id}

    def insert_outgoing_call_trunk(self, **kwargs):
        with self.inserter() as inserter:
            outgoing_call_trunk = OutcallTrunk(**kwargs)
            inserter.add_me(outgoing_call_trunk)
            return {'priority': outgoing_call_trunk.priority}

    def insert_call_filter(self, **kwargs):
        with self.inserter() as inserter:
            call_filter = inserter.add_call_filter(**kwargs)
            return {'id': call_filter.id}

    def insert_call_filter_member(self, **kwargs):
        with self.inserter() as inserter:
            call_filter_member = inserter.add_call_filter_member(**kwargs)
            return {'id': call_filter_member.id}

    def insert_group(self, **kwargs):
        with self.inserter() as inserter:
            group = inserter.add_group(**kwargs)
            return {
                'id': group.id,
                'tenant_uuid': group.tenant_uuid,
                'name': group.name,
            }

    def insert_group_user_member(self, userid: str, groupname: str, **kwargs):
        with self.inserter() as inserter:
            member = inserter.add_queue_member(
                queue_name=groupname,
                userid=userid,
                usertype='user',
                category='group',
                **kwargs,
            )
            member.fix()
            return {
                'interface': member.interface,
                'queue_name': member.queue_name,
                'position': member.position,
                'exten': member.exten,
                'context': member.context,
            }

    def insert_group_extension_member(
        self, exten: str, context: str, groupname: str, **kwargs
    ):
        with self.inserter() as inserter:
            member = inserter.add_queue_member(
                queue_name=groupname,
                userid=0,
                usertype='user',
                category='group',
                exten=exten,
                context=context,
                **kwargs,
            )
            member.fix()
            return {
                'interface': member.interface,
                'queue_name': member.queue_name,
                'position': member.position,
                'exten': member.exten,
                'context': member.context,
            }

    def insert_dial_action(self, **kwargs):
        with self.inserter() as inserter:
            dial_action = inserter.add_dialaction(**kwargs)
            return {
                'category': dial_action.category,
                'categoryval': dial_action.categoryval,
            }
