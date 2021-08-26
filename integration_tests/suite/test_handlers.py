# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from .helpers.base import IntegrationTest, use_asset


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
        recv_vars, recv_cmds = self.agid.incoming_user_set_features(variables)

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

    @pytest.mark.skip('NotImplemented: need agentd mock')
    def test_agent_get_status(self):
        with self.db.queries() as queries:
            agent = queries.insert_agent()

        recv_vars, recv_cmds = self.agid.agent_get_status(
            agent['tenant_uuid'],
            agent['id'],
        )

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_AGENT_LOGIN_STATUS'] == 'logged_in'

    @pytest.mark.skip('NotImplemented: need agentd mock')
    def test_agent_login(self):
        with self.db.queries() as queries:
            agent = queries.insert_agent()
            extension = queries.insert_extension()

        recv_vars, recv_cmds = self.agid.agent_login(
            agent['tenant_uuid'],
            agent['id'],
            extension['exten'],
            extension['context'],
        )

        assert recv_cmds['FAILURE'] is False
        assert recv_vars['XIVO_AGENTSTATUS'] == 'logged'

    @pytest.mark.skip('NotImplemented: need agentd mock')
    def test_agent_logoff(self):
        with self.db.queries() as queries:
            agent = queries.insert_agent()

        recv_vars, recv_cmds = self.agid.agent_logoff(
            agent['tenant_uuid'],
            agent['id'],
        )

        assert recv_cmds['FAILURE'] is False

    @pytest.mark.skip('NotImplemented: need to verify file on filesystem')
    def test_callback(self):
        pass

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

    @pytest.mark.skip('NotImplemented')
    def test_callfilter(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_call_recording(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_check_diversion(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_check_schedule(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_convert_pre_dial_handler(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_fwdundoall(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_getring(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_get_user_interfaces(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_group_answered_call(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_group_member(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_handler_fax(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_in_callerid(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_incoming_agent_set_features(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_incoming_conference_set_features(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_incoming_did_set_features(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_incoming_group_set_features(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_incoming_queue_set_features(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_outgoing_user_set_features(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_paging(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_phone_get_features(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_phone_progfunckey_devstate(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_phone_progfunckey(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_provision(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_queue_answered_call(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_queue_skill_rule_set(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_user_get_vmbox(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_user_set_call_rights(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_vmbox_get_info(self):
        pass

    @pytest.mark.skip('NotImplemented')
    def test_wake_mobile(self):
        pass
