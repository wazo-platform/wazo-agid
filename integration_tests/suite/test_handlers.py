# Copyright 2021-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
import re
import pytest
from textwrap import dedent
from hamcrest import assert_that, calling, raises
from .helpers.base import IntegrationTest, use_asset
from .helpers.agid import AGIFailException


@use_asset('base')
class TestHandlers(IntegrationTest):
    def test_monitoring(self):
        recv_vars, recv_cmds = self.agid.monitoring()
        assert recv_cmds['Status'] == 'OK'

    def test_incoming_user_set_features_with_dstid(self):
        with self.db.queries() as queries:
            sip = queries.insert_endpoint_sip()
            user, line, extension = queries.insert_user_line_extension(
                firstname='Firstname',
                lastname='Lastname',
                exten='1801',
                endpoint_sip_uuid=sip['uuid'],
            )

        variables = {
            'XIVO_USERID': user['id'],
            'XIVO_DSTID': user['id'],
            'XIVO_DST_EXTEN_ID': extension['id'],
            'XIVO_CALLORIGIN': 'patate',
            'XIVO_SRCNUM': extension['exten'],
            'XIVO_DSTNUM': 1800,
            'XIVO_BASE_CONTEXT': extension['context'],
            'WAZO_USER_MOH_UUID': '',
            'WAZO_CALL_RECORD_ACTIVE': '0',
            'XIVO_FROMGROUP': '0',
            'XIVO_PATH': '',
            f'PJSIP_ENDPOINT({line["name"]},webrtc)': 'no',
            f'PJSIP_DIAL_CONTACTS({line["name"]})': 'contact',
            'CHANNEL(videonativeformat)': '1',
        }
        recv_vars, recv_cmds = self.agid.incoming_user_set_features(variables=variables)

        assert recv_cmds['FAILURE'] is False

        assert recv_vars['XIVO_DST_USERNUM'] == extension['exten']
        assert recv_vars['WAZO_DST_USER_CONTEXT'] == extension['context']
        assert recv_vars['WAZO_DST_NAME'] == 'Firstname Lastname'
        assert recv_vars['XIVO_DST_REDIRECTING_NAME'] == 'Firstname Lastname'
        assert recv_vars['XIVO_DST_REDIRECTING_NUM'] == extension['exten']
        assert recv_vars['WAZO_DST_UUID'] == user['uuid']
        assert recv_vars['WAZO_DST_TENANT_UUID'] == user['tenant_uuid']
        assert recv_vars['XIVO_INTERFACE'] == 'contact'
        assert recv_vars['XIVO_CALLOPTIONS'] == ''
        assert recv_vars['XIVO_SIMULTCALLS'] == str(user['simultcalls'])
        assert recv_vars['XIVO_RINGSECONDS'] == str(user['ringseconds'])
        assert recv_vars['XIVO_ENABLEDND'] == str(user['enablednd'])
        assert recv_vars['XIVO_ENABLEVOICEMAIL'] == str(user['enablevoicemail'])
        assert recv_vars['XIVO_MAILBOX'] == ''
        assert recv_vars['XIVO_MAILBOX_CONTEXT'] == ''
        assert recv_vars['XIVO_USEREMAIL'] == ''
        assert recv_vars['XIVO_ENABLEUNC'] == str(user['enableunc'])
        assert recv_vars['XIVO_FWD_USER_UNC_ACTION'] == 'none'
        assert recv_vars['XIVO_FWD_USER_UNC_ACTIONARG1'] == ''
        assert recv_vars['XIVO_FWD_USER_UNC_ACTIONARG2'] == ''
        assert recv_vars['XIVO_FWD_USER_BUSY_ACTION'] == 'none'
        assert recv_vars['XIVO_FWD_USER_BUSY_ISDA'] == '1'
        assert recv_vars['XIVO_FWD_USER_BUSY_ACTIONARG1'] == ''
        assert recv_vars['XIVO_FWD_USER_BUSY_ACTIONARG2'] == ''
        assert recv_vars['XIVO_FWD_USER_NOANSWER_ACTION'] == 'none'
        assert recv_vars['XIVO_FWD_USER_NOANSWER_ISDA'] == '1'
        assert recv_vars['XIVO_FWD_USER_NOANSWER_ACTIONARG1'] == ''
        assert recv_vars['XIVO_FWD_USER_NOANSWER_ACTIONARG2'] == ''
        assert recv_vars['XIVO_FWD_USER_CONGESTION_ACTION'] == 'none'
        assert recv_vars['XIVO_FWD_USER_CONGESTION_ISDA'] == '1'
        assert recv_vars['XIVO_FWD_USER_CONGESTION_ACTIONARG1'] == ''
        assert recv_vars['XIVO_FWD_USER_CONGESTION_ACTIONARG2'] == ''
        assert recv_vars['XIVO_FWD_USER_CHANUNAVAIL_ACTION'] == 'none'
        assert recv_vars['XIVO_FWD_USER_CHANUNAVAIL_ISDA'] == '1'
        assert recv_vars['XIVO_FWD_USER_CHANUNAVAIL_ACTIONARG1'] == ''
        assert recv_vars['XIVO_FWD_USER_CHANUNAVAIL_ACTIONARG2'] == ''
        assert recv_vars['CHANNEL(musicclass)'] == user['musiconhold']
        assert recv_vars['WAZO_CALL_RECORD_SIDE'] == 'caller'
        assert recv_vars['XIVO_USERPREPROCESS_SUBROUTINE'] == ''
        assert recv_vars['XIVO_MOBILEPHONENUMBER'] == ''
        assert recv_vars['WAZO_VIDEO_ENABLED'] == '1'
        assert recv_vars['XIVO_PATH'] == 'user'
        assert recv_vars['XIVO_PATH_ID'] == str(user['id'])

    def test_agent_get_options(self):
        with self.db.queries() as queries:
            agent = queries.insert_agent()

        recv_vars, recv_cmds = self.agid.agent_get_options(
            agent['tenant_uuid'],
            agent['number'],
        )

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_AGENTEXISTS'] == '1'
        assert recv_vars['XIVO_AGENTPASSWD'] == ''
        assert recv_vars['XIVO_AGENTID'] == str(agent['id'])
        assert recv_vars['XIVO_AGENTNUM'] == agent['number']
        assert recv_vars['CHANNEL(language)'] == agent['language']

    def test_agent_get_status(self):
        with self.db.queries() as queries:
            agent = queries.insert_agent()

        self.agentd.expect_get_agent_status(agent['id'], agent['tenant_uuid'])
        recv_vars, recv_cmds = self.agid.agent_get_status(
            agent['tenant_uuid'],
            agent['id'],
        )

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_AGENT_LOGIN_STATUS'] == 'logged_in'

        assert self.agentd.verify_get_agent_status_called(agent['id']) is True

    def test_agent_login(self):
        with self.db.queries() as queries:
            agent = queries.insert_agent()
            extension = queries.insert_extension()

        self.agentd.expect_agent_login(
            agent['id'], agent['tenant_uuid'], extension['context'], extension['exten'],
        )
        recv_vars, recv_cmds = self.agid.agent_login(
            agent['tenant_uuid'],
            agent['id'],
            extension['exten'],
            extension['context'],
        )

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_AGENTSTATUS'] == 'logged'

        assert self.agentd.verify_agent_login_called(agent['id']) is True

    def test_agent_logoff(self):
        with self.db.queries() as queries:
            agent = queries.insert_agent()

        self.agentd.expect_agent_logoff(agent['id'], agent['tenant_uuid'])

        recv_vars, recv_cmds = self.agid.agent_logoff(
            agent['tenant_uuid'],
            agent['id'],
        )

        assert recv_cmds['FAILURE'] is False
        assert self.agentd.verify_agent_logoff_called(agent['id']) is True

    def test_callback(self):
        pytest.xfail("Will fail until Wazo-578 is fixed")

        with self.db.queries() as queries:
            extension = queries.insert_extension()

        extension_number, context = extension['exten'], extension['context']
        variables = {
            'XIVO_SRCNUM': extension_number,
            'AST_CONFIG(asterisk.conf,directories,astspooldir)': '/var/spool/asterisk',
        }
        chown = f"asterisk:asterisk"
        self.filesystem.create_path('/var/spool/asterisk/tmp', chown=chown)
        self.filesystem.create_path('/var/spool/asterisk/outgoing', chown=chown)

        recv_vars, recv_cmds = self.agid.callback(context, variables=variables)
        assert recv_cmds['FAILURE'] is False

        file_name = self.filesystem.find_file('/var/spool/asterisk/outgoing/', f'{extension_number}-*.call')
        assert file_name
        assert self.filesystem.read_file(file_name) == dedent(f"""\
            Channel: Local/{extension_number}@{context}
            MaxRetries: 0
            RetryTime: 30
            WaitTime: 30
            CallerID: {extension_number}
            Set: XIVO_DISACONTEXT={context}
            Context: xivo-callbackdisa
            Extension: s
        """).strip('\n')

    def test_callerid_extend(self):
        recv_vars, recv_cmds = self.agid.callerid_extend('en')

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_SRCTON'] == 'en'

    def test_callerid_forphones_without_reverse_lookup(self):
        recv_vars, recv_cmds = self.agid.callerid_forphones(
            calleridname='name',
            callerid='numero',
        )

        assert recv_cmds['FAILURE'] is False

    def test_callfilter(self):
        with self.db.queries() as queries:
            user = queries.insert_user()
            call_filter = queries.insert_call_filter()
            call_filter_member = queries.insert_call_filter_member(
                type='user', typeval=user['id'], callfilterid=call_filter['id'], active=1
            )

        variables = {
            'XIVO_USERID': user['id'],
        }
        recv_vars, recv_cmds = self.agid.callfilter(call_filter_member['id'], variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_BSFILTERENABLED'] == '0'

    def test_call_recording_start(self):
        with self.db.queries() as queries:
            agent = queries.insert_agent()

        variables = {
            'WAZO_CALL_RECORD_ACTIVE': '0',
        }

        self.calld.expect_calls_record_start(1)

        recv_vars, recv_cmds = self.agid.call_recording(
            agi_channel=f'Local/id-{agent["id"]}@agentcallback-0000000a1;1',
            agi_uniqueid='1',
            variables=variables,
        )

        assert self.calld.verify_calls_record_start_called(1) is True
        self.calld.clear()

        assert recv_cmds['FAILURE'] is False

    def test_call_recording_stop(self):
        with self.db.queries() as queries:
            agent = queries.insert_agent()

        variables = {
            'WAZO_CALL_RECORD_ACTIVE': '1',
        }

        self.calld.expect_calls_record_stop(1)

        recv_vars, recv_cmds = self.agid.call_recording(
            agi_channel=f'Local/id-{agent["id"]}@agentcallback-0000000a1;1',
            agi_uniqueid='1',
            variables=variables,
        )

        assert self.calld.verify_calls_record_stop_called(1) is True
        self.calld.clear()

        assert recv_cmds['FAILURE'] is False

    def test_call_record_caller(self):
        with self.db.queries() as queries:
            agent = queries.insert_agent()
            user = queries.insert_user(agent_id=agent['id'], call_record_outgoing_internal_enabled=1)

        variables = {
            'WAZO_CALL_RECORD_ACTIVE': '0',
            'WAZO_USERUUID': user['uuid'],
            'WAZO_TENANT_UUID': agent['tenant_uuid'],
            'XIVO_CALLORIGIN': 'intern',
            'XIVO_OUTCALLID': '',
            'WAZO_MIXMONITOR_OPTIONS': 'mix-options',
        }

        recv_vars, recv_cmds = self.agid.record_caller(
            agi_channel=f'Local/id-{agent["id"]}@agentcallback-0000000a1;1',
            agi_uniqueid='1',
            variables=variables,
        )

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['WAZO_CALL_RECORD_ACTIVE'] == '1'
        assert re.match(
            rf'/var/lib/wazo/sounds/tenants/{agent["tenant_uuid"]}/monitor/[a-f0-9\-]{{36}}.wav,mix-options',
            recv_cmds['EXEC MixMonitor'],
        ) is not None

    def test_check_diversion_hold_time(self):
        queue_name = 'queue-wait-time'
        with self.db.queries() as queries:
            queue = queries.insert_queue_feature(name=queue_name, waittime=5)

        variables = {
            'XIVO_DSTID': queue['id'],
            f'QUEUE_WAITING_COUNT({queue_name})': '1',
            'QUEUEHOLDTIME': '6'
        }

        recv_vars, recv_cmds = self.agid.check_diversion(variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_DIVERT_EVENT'] == 'DIVERT_HOLDTIME'
        assert recv_vars['XIVO_FWD_TYPE'] == 'QUEUE_QWAITTIME'

    def test_check_diversion_wait_ratio(self):
        queue_name = 'queue-wait-ratio'
        with self.db.queries() as queries:
            queue = queries.insert_queue_feature(name=queue_name, waitratio=1.2)

        variables = {
            'XIVO_DSTID': queue['id'],
            f'QUEUE_WAITING_COUNT({queue_name})': '2',
            f'QUEUE_MEMBER({queue_name},logged)': '2',
        }

        recv_vars, recv_cmds = self.agid.check_diversion(variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_DIVERT_EVENT'] == 'DIVERT_CA_RATIO'
        assert recv_vars['XIVO_FWD_TYPE'] == 'QUEUE_QWAITRATIO'

    def test_check_schedule(self):
        with self.db.queries() as queries:
            user = queries.insert_user()
            schedule = queries.insert_schedule()
            schedule_path = queries.insert_schedule_path(schedule_id=schedule['id'], pathid=user['id'])
            queries.insert_schedule_time(mode='closed', schedule_id=schedule['id'])

        variables = {
            'XIVO_PATH': schedule_path['path'],
            'XIVO_PATH_ID': str(schedule_path['path_id']),
        }

        recv_vars, recv_cmds = self.agid.check_schedule(variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_SCHEDULE_STATUS'] == 'closed'
        assert recv_vars['XIVO_PATH'] == ''

    def test_convert_pre_dial_handler(self):
        variables = {
            'XIVO_CALLOPTIONS': 'Xb(foobaz^s^1)B(foobar^s^1)',
        }

        recv_vars, recv_cmds = self.agid.convert_pre_dial_handler(variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_CALLOPTIONS'] == 'XB(foobar^s^1)'
        assert recv_vars['PUSH(_WAZO_PRE_DIAL_HANDLERS,|)'] == 'foobaz,s,1'

    def test_fwdundoall(self):
        with self.db.queries() as queries:
            user = queries.insert_user()

        variables = {
            'XIVO_USERID': user['id'],
        }
        self.confd.expect_update_forwards(user['id'], {
            forward: {'enabled': False} for forward in ('busy', 'noanswer', 'unconditional')
        })
        recv_vars, recv_cmds = self.agid.fwdundoall(variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert self.confd.verify_update_forwards_called(user['id']) is True

    def test_getring(self):
        variables = {
            'XIVO_REAL_NUMBER': '1001',
            'XIVO_REAL_CONTEXT': 'default',
            'XIVO_CALLORIGIN': 'patate',
            'XIVO_FWD_REFERER': 'foo:bar',
            'XIVO_CALLFORWARDED': '1',
        }

        recv_vars, recv_cmds = self.agid.getring(variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_PHONETYPE'] == 'linksys'
        assert recv_vars['XIVO_RINGTYPE'] == 'test-ring'

    def test_get_user_interfaces(self):
        with self.db.queries() as queries:
            user, line_1, extension_1 = queries.insert_user_line_extension(
                exten='1802',
                endpoint_sip_uuid=queries.insert_endpoint_sip()['uuid'],
            )
            line_2 = queries.insert_line(typeval=user['id'])
            queries.insert_user_line(user['id'], line_2['id'])

        variables = {
            f'HINT({user["uuid"]}@usersharedlines)': f'sccp/{line_1["name"]}&pjsip/{line_2["name"]}',
            f'PJSIP_ENDPOINT({line_2["name"]},webrtc)': 'no',
            f'PJSIP_DIAL_CONTACTS({line_2["name"]})': 'contact',
        }
        recv_vars, recv_cmds = self.agid.get_user_interfaces(user['uuid'], variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['WAZO_USER_INTERFACES'] == f'sccp/{line_1["name"]}&contact'

    def test_group_answered_call(self):
        with self.db.queries() as queries:
            user = queries.insert_user(call_record_incoming_external_enabled=1)
            extension = queries.insert_extension(typeval=user['id'])
            line = queries.insert_line(
                typeval=user['id'],
                context=extension['context'],
                endpoint_sip_uuid=queries.insert_endpoint_sip()['uuid']
            )
            queries.insert_extension_line(extension['id'], line['id'])
            queries.insert_user_line(user['id'], line['id'], main_line=True)

        variables = {
            'WAZO_CALL_RECORD_ACTIVE': '0',
            'XIVO_CALLORIGIN': 'extern',
        }

        self.calld.expect_calls_record_start(1)

        recv_vars, recv_cmds = self.agid.group_answered_call(
            agi_channel=f'Local/{extension["exten"]}@{extension["context"]}-0000000a1;1',
            agi_uniqueid='1',
            variables=variables,
        )

        assert self.calld.verify_calls_record_start_called(1) is True
        self.calld.clear()

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['WAZO_RECORD_GROUP_CALLEE'] == '1'

    def test_group_member_add(self):
        self.confd.expect_groups_get(2, {'name': 'test-group'})

        recv_vars, recv_cmds = self.agid.group_member_add(
            'tenant-uuid',
            'user-uuid',
            '2',
        )

        assert self.confd.verify_groups_get_called(2) is True
        self.confd.clear()

        assert recv_cmds['FAILURE'] is False
        assert recv_cmds['EXEC AddQueueMember'] == 'test-group,Local/user-uuid@usersharedlines,,,,hint:user-uuid@usersharedlines'

    def test_group_member_present(self):
        self.confd.expect_groups_get(2, {'name': 'test-group'})

        recv_vars, recv_cmds = self.agid.group_member_present(
            'tenant-uuid',
            'user-uuid',
            '2',
            variables={
                'QUEUE_MEMBER_LIST(test-group)': 'Local/user-uuid@usersharedlines',
            }
        )

        assert self.confd.verify_groups_get_called(2) is True
        self.confd.clear()

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['WAZO_GROUP_MEMBER_PRESENT'] == '1'

    def test_group_member_remove(self):
        self.confd.expect_groups_get(2, {'name': 'test-group'})

        recv_vars, recv_cmds = self.agid.group_member_remove(
            'tenant-uuid',
            'user-uuid',
            '2',
        )

        assert self.confd.verify_groups_get_called(2) is True
        self.confd.clear()

        assert recv_cmds['FAILURE'] is False
        assert recv_cmds['EXEC RemoveQueueMember'] == 'test-group,Local/user-uuid@usersharedlines'

    def test_handle_fax(self):
        variables = {
            'XIVO_DSTNUM': 'default',
        }
        recv_vars, recv_cmds = self.agid.handle_fax(
            '/var/lib/wazo-agid/blank.tiff',
            'test@localhost',
            variables=variables
        )
        assert recv_cmds['FAILURE'] is False

        assert self.filesystem.read_file('/tmp/last_tiff2pdf_cmd.txt') == \
            '-o /var/lib/wazo-agid/blank.pdf /var/lib/wazo-agid/blank.tiff'

        assert self.filesystem.read_file('/tmp/last_mutt_cmd.txt') == (
            '-e set copy=no '
            '-e set from=no-reply+fax@wazo.community '
            '-e set realname=\'Wazo Fax\' '
            '-e set use_from=yes '
            '-s Reception de FAX vers default '
            '-a /var/lib/wazo-agid/blank.pdf -- test@localhost'
        )

    def test_in_callerid(self):
        number = '+155555555555'
        recv_vars, recv_cmds = self.agid.in_callerid(
            agi_callerid=number,
            agi_calleridname=number,
        )
        assert recv_cmds['FAILURE'] is False
        assert recv_vars['CALLERID(all)'] == '\\"00155555555555\\" <00155555555555>'

    def test_incoming_agent_set_features(self):
        with self.db.queries() as queries:
            agent = queries.insert_agent(preprocess_subroutine='test-subroutine')
            queries.insert_agent_login_status(agent_id=agent['id'], state_interface='test-device')

        variables = {
            'XIVO_QUEUEOPTIONS': 'hitPwxk',
        }
        recv_vars, recv_cmds = self.agid.incoming_agent_set_features(
            agent['id'],
            variables=variables
        )
        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_AGENT_INTERFACE'] == 'test-device'
        assert recv_vars['XIVO_AGENTPREPROCESS_SUBROUTINE'] == 'test-subroutine'
        assert recv_vars['XIVO_QUEUECALLOPTIONS'] == 'hitwxk'

    def test_incoming_conference_set_features(self):
        name = u'My Conférence'
        with self.db.queries() as queries:
            conference = queries.insert_conference(name=name)

        variables = {
            'XIVO_DSTID': conference['id'],
        }
        recv_vars, recv_cmds = self.agid.incoming_conference_set_features(variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['WAZO_CONFBRIDGE_ID'] == str(conference['id'])
        assert recv_vars['WAZO_CONFBRIDGE_TENANT_UUID'] == conference['tenant_uuid']
        assert recv_vars['WAZO_CONFBRIDGE_BRIDGE_PROFILE'] == f'xivo-bridge-profile-{conference["id"]}'
        assert recv_vars['WAZO_CONFBRIDGE_USER_PROFILE'] == f'xivo-user-profile-{conference["id"]}'
        assert recv_vars['WAZO_CONFBRIDGE_MENU'] == 'xivo-default-user-menu'
        assert recv_vars['WAZO_CONFBRIDGE_PREPROCESS_SUBROUTINE'] == ''
        assert recv_cmds['EXEC CELGenUserEvent'] == f'WAZO_CONFERENCE, NAME: {name}'

    def test_incoming_did_set_features(self):
        with self.db.queries() as queries:
            call = queries.insert_incoming_call(preprocess_subroutine='test-subroutine', greeting_sound='test-sound')
            extension = queries.insert_extension(type='incall', typeval=call['id'])

        variables = {
            'XIVO_INCALL_ID': call['id'],
            'XIVO_DSTID': call['id'],
        }
        recv_vars, recv_cmds = self.agid.incoming_did_set_features(variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_DIDPREPROCESS_SUBROUTINE'] == 'test-subroutine'
        assert recv_vars['XIVO_EXTENPATTERN'] == extension['exten']
        assert recv_vars['XIVO_PATH'] == 'incall'
        assert recv_vars['XIVO_PATH_ID'] == str(call['id'])
        assert recv_vars['XIVO_REAL_CONTEXT'] == extension['context']
        assert recv_vars['XIVO_REAL_NUMBER'] == extension['exten']
        assert recv_vars['WAZO_GREETING_SOUND'] == 'test-sound'

    def test_incoming_group_set_features(self):
        with self.db.queries() as queries:
            group = queries.insert_group(name='incoming_group_set_features', timeout=25)
            extension = queries.insert_extension(type='group', typeval=group['id'])
            for event in ('noanswer', 'congestion', 'busy', 'chanunavail'):
                queries.insert_dial_action(
                    event=event,
                    category='group',
                    categoryval=group['id'],
                    action='group',
                    actionarg1=f'{event}-actionarg1',
                    actionarg2=f'{event}-actionarg2',
                )

        variables = {
            'XIVO_DSTID': group['id'],
            'XIVO_FWD_REFERER': group['id'],
            'XIVO_PATH': None,
        }
        recv_vars, recv_cmds = self.agid.incoming_group_set_features(variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_GROUPOPTIONS'] == 'ir'
        assert recv_vars['XIVO_GROUPNEEDANSWER'] == '0'
        assert recv_vars['XIVO_REAL_NUMBER'] == extension['exten']
        assert recv_vars['XIVO_REAL_CONTEXT'] == extension['context']
        assert recv_vars['XIVO_GROUPNAME'] == 'incoming_group_set_features'
        assert recv_vars['XIVO_GROUPTIMEOUT'] == '25'

        assert recv_vars['XIVO_FWD_GROUP_NOANSWER_ACTION'] == 'group'
        assert recv_vars['XIVO_FWD_GROUP_NOANSWER_ISDA'] == '1'
        assert recv_vars['XIVO_FWD_GROUP_NOANSWER_ACTIONARG1'] == 'noanswer-actionarg1'
        assert recv_vars['XIVO_FWD_GROUP_NOANSWER_ACTIONARG2'] == 'noanswer-actionarg2'
        assert recv_vars['XIVO_FWD_GROUP_CONGESTION_ACTION'] == 'group'
        assert recv_vars['XIVO_FWD_GROUP_CONGESTION_ISDA'] == '1'
        assert recv_vars['XIVO_FWD_GROUP_CONGESTION_ACTIONARG1'] == 'congestion-actionarg1'
        assert recv_vars['XIVO_FWD_GROUP_CONGESTION_ACTIONARG2'] == 'congestion-actionarg2'
        assert recv_vars['XIVO_FWD_GROUP_BUSY_ACTION'] == 'group'
        assert recv_vars['XIVO_FWD_GROUP_BUSY_ISDA'] == '1'
        assert recv_vars['XIVO_FWD_GROUP_BUSY_ACTIONARG1'] == 'busy-actionarg1'
        assert recv_vars['XIVO_FWD_GROUP_BUSY_ACTIONARG2'] == 'busy-actionarg2'
        assert recv_vars['XIVO_FWD_GROUP_CHANUNAVAIL_ACTION'] == 'group'
        assert recv_vars['XIVO_FWD_GROUP_CHANUNAVAIL_ISDA'] == '1'
        assert recv_vars['XIVO_FWD_GROUP_CHANUNAVAIL_ACTIONARG1'] == 'chanunavail-actionarg1'
        assert recv_vars['XIVO_FWD_GROUP_CHANUNAVAIL_ACTIONARG2'] == 'chanunavail-actionarg2'

        assert recv_vars['XIVO_PATH'] == 'group'
        assert recv_vars['XIVO_PATH_ID'] == str(group['id'])
        assert recv_vars['WAZO_CALL_RECORD_SIDE'] == 'caller'
        assert re.match(r'^[a-f0-9\-]{36}$', recv_vars['__WAZO_LOCAL_CHAN_MATCH_UUID']) is not None

    def test_incoming_queue_set_features(self):
        with self.db.queries() as queries:
            queue = queries.insert_queue_feature(
                number='1234',
                context='default',
                timeout=25,
                data_quality=1,
                hitting_callee=1,
                hitting_caller=1,
                retries=1,
                ring=1,
                transfer_user=1,
                transfer_call=1,
                write_caller=1,
                write_calling=1,
                ignore_forward=1,
                mark_answered_elsewhere=1,
            )
            for event in ('noanswer', 'congestion', 'busy', 'chanunavail'):
                queries.insert_dial_action(
                    event=event,
                    category='queue',
                    categoryval=queue['id'],
                    action='queue',
                    actionarg1=f'{event}-actionarg1',
                    actionarg2=f'{event}-actionarg2',
                )

        variables = {
            'XIVO_DSTID': queue['id'],
            'XIVO_FWD_REFERER': queue['id'],
            'XIVO_PATH': '',
        }
        recv_vars, recv_cmds = self.agid.incoming_queue_set_features(variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_REAL_NUMBER'] == queue['number'] or None
        assert recv_vars['XIVO_REAL_CONTEXT'] == 'default'
        assert recv_vars['XIVO_QUEUENAME'] == queue['name']
        assert recv_vars['XIVO_QUEUEOPTIONS'] == 'dhHnrtTxXiC'
        assert recv_vars['XIVO_QUEUENEEDANSWER'] == '0'
        assert recv_vars['XIVO_QUEUEURL'] == queue['url']
        assert recv_vars['XIVO_QUEUEANNOUNCEOVERRIDE'] == queue['url']
        assert recv_vars['XIVO_QUEUEPREPROCESS_SUBROUTINE'] == queue['url']
        assert recv_vars['XIVO_QUEUETIMEOUT'] == '25'

        assert recv_vars['XIVO_FWD_QUEUE_NOANSWER_ACTION'] == 'queue'
        assert recv_vars['XIVO_FWD_QUEUE_NOANSWER_ISDA'] == '1'
        assert recv_vars['XIVO_FWD_QUEUE_NOANSWER_ACTIONARG1'] == 'noanswer-actionarg1'
        assert recv_vars['XIVO_FWD_QUEUE_NOANSWER_ACTIONARG2'] == 'noanswer-actionarg2'
        assert recv_vars['XIVO_FWD_QUEUE_CONGESTION_ACTION'] == 'queue'
        assert recv_vars['XIVO_FWD_QUEUE_CONGESTION_ISDA'] == '1'
        assert recv_vars['XIVO_FWD_QUEUE_CONGESTION_ACTIONARG1'] == 'congestion-actionarg1'
        assert recv_vars['XIVO_FWD_QUEUE_CONGESTION_ACTIONARG2'] == 'congestion-actionarg2'
        assert recv_vars['XIVO_FWD_QUEUE_BUSY_ACTION'] == 'queue'
        assert recv_vars['XIVO_FWD_QUEUE_BUSY_ISDA'] == '1'
        assert recv_vars['XIVO_FWD_QUEUE_BUSY_ACTIONARG1'] == 'busy-actionarg1'
        assert recv_vars['XIVO_FWD_QUEUE_BUSY_ACTIONARG2'] == 'busy-actionarg2'
        assert recv_vars['XIVO_FWD_QUEUE_CHANUNAVAIL_ACTION'] == 'queue'
        assert recv_vars['XIVO_FWD_QUEUE_CHANUNAVAIL_ISDA'] == '1'
        assert recv_vars['XIVO_FWD_QUEUE_CHANUNAVAIL_ACTIONARG1'] == 'chanunavail-actionarg1'
        assert recv_vars['XIVO_FWD_QUEUE_CHANUNAVAIL_ACTIONARG2'] == 'chanunavail-actionarg2'

        assert recv_vars['XIVO_QUEUESTATUS'] == 'ok'
        assert recv_vars['XIVO_PATH'] == 'queue'
        assert recv_vars['XIVO_PATH_ID'] == str(queue['id'])
        assert recv_vars['XIVO_PICKUPGROUP'] == ''
        assert recv_vars['WAZO_CALL_RECORD_SIDE'] == 'caller'
        assert re.match(r'^[a-f0-9\-]{36}$', recv_vars['__WAZO_LOCAL_CHAN_MATCH_UUID']) is not None

    def test_outgoing_user_set_features(self):
        with self.db.queries() as queries:
            user = queries.insert_user(outcallerid='anonymous', enablexfer=1)
            call = queries.insert_outgoing_call(preprocess_subroutine='test-subroutine', hangupringtime=10)
            sip = queries.insert_endpoint_sip()
            trunk = queries.insert_trunk(endpoint_sip_uuid=sip['uuid'])
            queries.insert_outgoing_call_trunk(outcallid=call['id'], trunkfeaturesid=trunk['id'])

            dial_pattern = queries.insert_dial_pattern(typeid=call['id'])
            extension = queries.insert_extension(type='outcall', typeval=call['id'])

        variables = {
            'XIVO_USERID': user['id'],
            'WAZO_USERUUID': user['uuid'],
            'XIVO_DSTID': dial_pattern['id'],
            'XIVO_DSTNUM': extension['exten'],
            'XIVO_SRCNUM': extension['exten'],
            'XIVO_BASE_CONTEXT': extension['context'],
            'WAZO_TENANT_UUID': '',
            'XIVO_PATH': '',
        }
        recv_vars, recv_cmds = self.agid.outgoing_user_set_features(
            agi_channel='test',
            variables=variables
        )

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_CALLOPTIONS'] == 'T'
        assert recv_vars['CHANNEL(musicclass)'] == 'default'
        assert recv_vars['XIVO_INTERFACE0'] == 'PJSIP'
        assert recv_vars['XIVO_TRUNKEXTEN0'] == f'{extension["exten"]}@{sip["name"]}'
        assert recv_vars['XIVO_TRUNKSUFFIX0'] == ''
        assert recv_vars['XIVO_OUTCALLPREPROCESS_SUBROUTINE'] == 'test-subroutine'
        assert recv_vars['XIVO_HANGUPRINGTIME'] == '10'
        assert recv_vars['XIVO_OUTCALLID'] == str(call['id'])
        assert recv_vars['XIVO_PATH'] == 'outcall'
        assert recv_vars['XIVO_PATH_ID'] == str(call['id'])
        assert recv_vars['WAZO_CALL_RECORD_SIDE'] == 'caller'
        assert recv_vars['CALLERID(name-pres)'] == 'prohib'
        assert recv_vars['CALLERID(num-pres)'] == 'prohib'

    def test_meeting_user(self):
        with self.db.queries() as queries:
            meeting = queries.insert_meeting()

        variables = {
            'WAZO_TENANT_UUID': meeting['tenant_uuid'],
        }

        # Lookup by UUID
        recv_vars, recv_cmds = self.agid.meeting_user(
            'wazo-meeting-{uuid}'.format(**meeting),
            variables=variables,
        )

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['WAZO_MEETING_NAME'] == meeting['name']
        assert recv_vars['WAZO_MEETING_UUID'] == meeting['uuid']

        # Lookup by number
        recv_vars, recv_cmds = self.agid.meeting_user(
            meeting['number'],
            variables=variables,
        )

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['WAZO_MEETING_NAME'] == meeting['name']
        assert recv_vars['WAZO_MEETING_UUID'] == meeting['uuid']

    def test_paging(self):
        with self.db.queries() as queries:
            user = queries.insert_user()
            sip = queries.insert_endpoint_sip()
            paging = queries.insert_paging(
                timeout=25,
                duplex=1,
                ignore=1,
                quiet=1,
                record=1,
                commented=0,
                announcement_play=1,
                announcement_file='sounds.wav',
            )
            queries.insert_paging_user(userfeaturesid=user['id'], pagingid=paging['id'], caller=1)
            queries.insert_paging_user(userfeaturesid=user['id'], pagingid=paging['id'], caller=0)
            line_1 = queries.insert_line(typeval=user['id'], endpoint_sip_uuid=sip['uuid'])
            line_2 = queries.insert_line(typeval=user['id'], endpoint_sip_uuid=sip['uuid'])
            queries.insert_user_line(user['id'], line_1['id'])
            queries.insert_user_line(user['id'], line_2['id'])

        variables = {
            'XIVO_USERID': user['id'],
        }

        recv_vars, recv_cmds = self.agid.paging(
            paging['number'],
            variables=variables,
        )

        assert recv_cmds['FAILURE'] is False
        assert f'PJSIP/{line_1["name"]}' in recv_vars['XIVO_PAGING_LINES']
        assert f'PJSIP/{line_2["name"]}' in recv_vars['XIVO_PAGING_LINES']
        assert recv_vars['XIVO_PAGING_TIMEOUT'] == '25'
        assert recv_vars['XIVO_PAGING_OPTS'] == (
            f'sb(paging^add-sip-headers^1)dqri'
            f'A(/var/lib/wazo/sounds/tenants/{paging["tenant_uuid"]}/playback/sounds.wav)'
        )

    def test_phone_get_features(self):
        with self.db.queries() as queries:
            context = 'test-context'
            voicemail = queries.insert_voicemail(context=context, skipcheckpass='1')
            user = queries.insert_user(
                enablevoicemail=1,
                voicemailid=voicemail['id'],
                enableonlinerec=1,
                call_record_outgoing_external_enabled=1,
                call_record_outgoing_internal_enabled=1,
                call_record_incoming_external_enabled=1,
                call_record_incoming_internal_enabled=1,
                incallfilter=1,
                enablednd=1,
            )
        variables = {
            'XIVO_USERID': user['id'],
        }
        # Lookup by UUID
        self.confd.expect_forwards(user['id'], {
            "busy": {
                "destination": "dest-busy",
                "enabled": True
            },
            "noanswer": {
                "destination": "dest-noanswer",
                "enabled": True
            },
            "unconditional": {
                "destination": "dest-unconditional",
                "enabled": False
            }
        })
        recv_vars, recv_cmds = self.agid.phone_get_features(variables=variables)

        assert recv_cmds['FAILURE'] is False

        assert recv_vars['XIVO_ENABLEVOICEMAIL'] == '1'
        assert recv_vars['XIVO_CALLRECORD'] == '1'
        assert recv_vars['XIVO_INCALLFILTER'] == '1'
        assert recv_vars['XIVO_ENABLEDND'] == '1'

        assert recv_vars['XIVO_ENABLEBUSY'] == '1'
        assert recv_vars['XIVO_DESTBUSY'] == 'dest-busy'
        assert recv_vars['XIVO_ENABLERNA'] == '1'
        assert recv_vars['XIVO_DESTRNA'] == 'dest-noanswer'
        assert recv_vars['XIVO_ENABLEUNC'] == '0'
        assert recv_vars['XIVO_DESTUNC'] == 'dest-unconditional'

    def test_phone_progfunckey_devstate(self):
        with self.db.queries() as queries:
            user = queries.insert_user()
            extension = queries.insert_extension(typeval='agentstaticlogin')

        variables = {
            'XIVO_USERID': user['id'],
        }

        recv_vars, recv_cmds = self.agid.phone_progfunckey_devstate(
            'agentstaticlogin',
            'ONHOLD',
            'dest',
            variables=variables,
        )

        assert recv_cmds['FAILURE'] is False
        assert recv_vars[f'DEVICE_STATE(Custom:*735{user["id"]}*{extension["exten"]}*dest)'] == 'ONHOLD'

    def test_phone_progfunckey(self):
        with self.db.queries() as queries:
            user = queries.insert_user()
            extension = queries.insert_extension(typeval='fwdbusy')

        variables = {
            'XIVO_USERID': user['id'],
        }

        recv_vars, recv_cmds = self.agid.phone_progfunckey(
            f'{user["id"]}*{extension["exten"]}',
            variables=variables,
        )

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_PHONE_PROGFUNCKEY'] == extension["exten"]
        assert recv_vars['XIVO_PHONE_PROGFUNCKEY_FEATURE'] == 'fwdbusy'

    def test_provision_autoprov(self):
        self.confd.expect_devices({
            'items': [{
                "ip": "192.168.1.1",
                "id": 1,
            }],
            'total': 1,
        })
        self.confd.expect_devices_autoprov(1)
        self.confd.expect_devices_synchronize(1)

        recv_vars, recv_cmds = self.agid.provision(
            'autoprov',
            '192.168.1.1:1234',
        )

        assert self.confd.verify_devices_called() is True
        assert self.confd.verify_devices_autoprov_called(1) is True
        assert self.confd.verify_devices_synchronize_called(1) is True
        self.confd.clear()

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_PROV_OK'] == '1'

    def test_provision_add_device(self):
        self.confd.expect_devices({
            'items': [{
                "ip": "192.168.1.2",
                "id": 2,
            }],
            'total': 1,
        })
        self.confd.expect_lines({
            'items': [{"id": 1}],
            'total': 1,
        })
        self.confd.expect_lines_devices(1, 2)
        self.confd.expect_devices_synchronize(2)

        recv_vars, recv_cmds = self.agid.provision(
            '123',
            '192.168.1.2:1234',
        )

        assert self.confd.verify_devices_called() is True
        assert self.confd.verify_lines_called() is True
        assert self.confd.verify_lines_devices_called(1, 2) is True
        assert self.confd.verify_devices_synchronize_called(2) is True
        self.confd.clear()
        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_PROV_OK'] == '1'

    def test_queue_answered_call(self):
        with self.db.queries() as queries:
            agent = queries.insert_agent()
            queries.insert_user(agent_id=agent['id'], call_record_incoming_external_enabled=1)

        variables = {
            'WAZO_CALL_RECORD_ACTIVE': '0',
            'XIVO_CALLORIGIN': 'extern',
        }

        self.calld.expect_calls_record_start(1)

        recv_vars, recv_cmds = self.agid.queue_answered_call(
            agi_channel=f'Local/id-{agent["id"]}@agentcallback-0000000a1;1',
            agi_uniqueid='1',
            variables=variables,
        )

        assert self.calld.verify_calls_record_start_called(1) is True
        self.calld.clear()

        assert recv_cmds['FAILURE'] is False

    def test_queue_skill_rule_set(self):
        with self.db.queries() as queries:
            skill_rule = queries.insert_queue_skill_rule()

        recv_vars, recv_cmds = self.agid.queue_skill_rule_set('queue_skill_rule_set', variables={
            'ARG2': f'timeout;{skill_rule["id"]};{{"opt1":1|"opt2": "val2"}}',
            'XIVO_QUEUESKILLRULESET': 'call'
        })

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_QUEUESKILLRULESET'] == f'skillrule-{skill_rule["id"]}(opt1=1,opt2=val2)'
        assert recv_vars['ARG2_TIMEOUT'] == 'timeout'

    def test_switchboard_set_features_no_switchboard(self):
        assert_that(
            calling(self.agid.switchboard_set_features).with_args('switchboard-not-found'),
            raises(AGIFailException)
        )

    def test_switchboard_set_features_fallback_no_fallback(self):
        with self.db.queries() as queries:
            switchboard = queries.insert_switchboard()

        recv_vars, recv_cmds = self.agid.switchboard_set_features(switchboard['uuid'])

        assert recv_cmds['FAILURE'] is False
        # resetting those variables is important when chaining switchboard forwards
        assert recv_vars['WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTION'] == ''
        assert recv_vars['WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTIONARG1'] == ''
        assert recv_vars['WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTIONARG2'] == ''

    def test_switchboard_set_features_with_fallback(self):
        with self.db.queries() as queries:
            fallbacks = {
                'noanswer': {'event': 'noanswer', 'action': 'user', 'actionarg1': '1', 'actionarg2': '2'}
            }
            switchboard = queries.insert_switchboard(fallbacks=fallbacks)

        recv_vars, recv_cmds = self.agid.switchboard_set_features(switchboard['uuid'])

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTION'] == 'user'
        assert recv_vars['WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTIONARG1'] == '1'
        assert recv_vars['WAZO_SWITCHBOARD_FALLBACK_NOANSWER_ACTIONARG2'] == '2'
        assert recv_vars['WAZO_SWITCHBOARD_TIMEOUT'] == ''

    def test_switchboard_set_features_with_timeout(self):
        with self.db.queries() as queries:
            switchboard = queries.insert_switchboard(timeout=42)

        recv_vars, recv_cmds = self.agid.switchboard_set_features(switchboard['uuid'])

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['WAZO_SWITCHBOARD_TIMEOUT'] == '42'

    def test_user_get_vmbox(self):
        with self.db.queries() as queries:
            context = 'test-context'
            voicemail = queries.insert_voicemail(context=context, skipcheckpass='1')
            user, line, extension = queries.insert_user_line_extension(
                enablevoicemail=1, voicemail_id=voicemail['id'], context=context,
            )

        variables = {
            'XIVO_USERID': user['id'],
            'XIVO_BASE_CONTEXT': context,
        }
        recv_vars, recv_cmds = self.agid.user_get_vmbox(extension['exten'], variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_VMMAIN_OPTIONS'] == 's'
        assert recv_vars['XIVO_MAILBOX'] == voicemail['mailbox']
        assert recv_vars['XIVO_MAILBOX_CONTEXT'] == context

    def test_user_set_call_rights(self):
        with self.db.queries() as queries:
            context = 'test-context'
            user, line, extension = queries.insert_user_line_extension(context=context)
            call_permission = queries.insert_call_permission(passwd='test')
            queries.insert_call_extension_permission(rightcallid=call_permission['id'], exten=extension['exten'])
            queries.insert_user_call_permission(typeval=user['id'], rightcallid=call_permission['id'])

        variables = {
            'XIVO_USERID': user['id'],
            'XIVO_DSTNUM': extension['exten'],
            'XIVO_OUTCALLID': context,
        }
        recv_vars, recv_cmds = self.agid.user_set_call_rights(extension['exten'], variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_AUTHORIZATION'] == 'DENY'

    def test_vmbox_get_info(self):
        with self.db.queries() as queries:
            context = 'default'
            voicemail = queries.insert_voicemail(context=context, skipcheckpass='1')
            user, line, extension = queries.insert_user_line_extension(
                enablevoicemail=1, voicemail_id=voicemail['id'], context=context,
            )

        variables = {
            'XIVO_USERID': user['id'],
            'XIVO_VMBOXID': voicemail['id'],
            'XIVO_BASE_CONTEXT': context,
        }
        recv_vars, recv_cmds = self.agid.vmbox_get_info(voicemail['mailbox'], variables=variables)

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_VMMAIN_OPTIONS'] == 's'
        assert recv_vars['XIVO_MAILBOX'] == voicemail['mailbox']
        assert recv_vars['XIVO_MAILBOX_CONTEXT'] == context
        assert recv_vars['XIVO_MAILBOX_LANGUAGE'] == 'fr_FR'

    def test_wake_mobile(self):
        with self.db.queries() as queries:
            user = queries.insert_user()

        variables = {
            'WAZO_WAIT_FOR_MOBILE': '1',
            'WAZO_VIDEO_ENABLED': '1',
        }
        recv_cmds = self.agid.wake_mobile(user['uuid'], variables=variables)[1]

        assert recv_cmds['FAILURE'] is False
        assert recv_cmds['EXEC UserEvent'] == f'Pushmobile,WAZO_DST_UUID: {user["uuid"]},WAZO_VIDEO_ENABLED: 1'
