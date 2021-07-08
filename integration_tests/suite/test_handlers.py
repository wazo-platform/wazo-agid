# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from .helpers.base import IntegrationTest, use_asset


@use_asset('base')
class TestHandlers(IntegrationTest):
    def test_monitoring(self):
        recv_vars, recv_cmds = self.agid.monitoring()
        assert recv_cmds['Status'] == 'OK'

    def test_incoming_user_set_features(self):
        variables = {
            'XIVO_USERID': 42,
            'XIVO_DSTID': 42,
            'XIVO_DST_EXTEN_ID': 42,
            'XIVO_CALLORIGIN': 42,
            'XIVO_SRCNUM': 1801,
            'XIVO_DSTNUM': 1800,
            'XIVO_BASE_CONTEXT': 'internal',
            'WAZO_USER_MOH_UUID': ''
        }
        recv_vars, recv_cmds = self.agid.incoming_user_set_features(variables)
        print(recv_vars)
        print(recv_cmds)
