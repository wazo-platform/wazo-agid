from .mock_clients import MockServerClient


class AgentdMockClient(MockServerClient):
    def __init__(self, host, port, version='1.0'):
        super().__init__(host, port, version)

    def expect_agent_login(self, agent_id, tenant_uuid, context, extension):
        self.simple_expectation(
            'POST',
            f'/agents/by-id/{agent_id}/login',
            204,
            {'context': context, 'extension': extension},
            headers={'Wazo-Tenant': tenant_uuid},
        )

    def expect_agent_logoff(self, agent_id, tenant_uuid):
        self.simple_expectation(
            'POST',
            f'/agents/by-id/{agent_id}/logoff',
            204,
            {},
            headers={'Wazo-Tenant': tenant_uuid},
        )

    def expect_get_agent_status(self, agent_id, tenant_uuid):
        self.simple_expectation(
            'GET',
            f'/agents/by-id/{agent_id}',
            200,
            {
                'id': agent_id,
                'logged': True,
                'paused': False,
                'origin_uuid': 'test-uuid',
                'context': 'default',
                'number': '12345',
                'extension': '12345',
                'state_interface': 'interface',
            },
            headers={'Wazo-Tenant': tenant_uuid},
        )

    def verify_agent_login_called(self, agent_id):
        return (
            self.verify_called('POST', f'/agents/by-id/{agent_id}/login').status_code
            == 202
        )

    def verify_agent_logoff_called(self, agent_id):
        return (
            self.verify_called('POST', f'/agents/by-id/{agent_id}/logoff').status_code
            == 202
        )

    def verify_get_agent_status_called(self, agent_id):
        return self.verify_called('GET', f'/agents/by-id/{agent_id}').status_code == 202
