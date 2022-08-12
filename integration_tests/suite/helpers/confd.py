from .mock_clients import MockServerClient


class ConfdMockClient(MockServerClient):
    def __init__(self, host, port, version='1.0'):
        super().__init__(host, port, version)

    def expect_forwards(self, user_id, forwards):
        self.simple_expectation('GET', f'/users/{user_id}/forwards', 200, forwards)

    def expect_update_forwards(self, user_id, forwards):
        self.simple_expectation('PUT', f'/users/{user_id}/forwards', 204, forwards)

    def verify_update_forwards_called(self, user_id):
        return self.verify_called('PUT', f'/users/{user_id}/forwards').status_code == 202
