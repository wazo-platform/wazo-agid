# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

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
