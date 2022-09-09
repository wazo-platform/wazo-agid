from .mock_clients import MockServerClient


class ConfdMockClient(MockServerClient):
    def __init__(self, host, port, version='1.0'):
        super().__init__(host, port, version)

    def expect_forwards(self, user_id, forwards):
        self.simple_expectation('GET', f'/users/{user_id}/forwards', 200, forwards)

    def expect_update_forwards(self, user_id, forwards):
        self.simple_expectation('PUT', f'/users/{user_id}/forwards', 204, forwards)

    def verify_update_forwards_called(self, user_id):
        return (
            self.verify_called('PUT', f'/users/{user_id}/forwards').status_code == 202
        )

    def expect_devices(self, devices):
        self.simple_expectation('GET', '/devices', 200, devices)

    def verify_devices_called(self):
        return self.verify_called('GET', '/devices').status_code == 202

    def expect_devices_autoprov(self, device_id):
        self.simple_expectation('GET', f'/devices/{device_id}/autoprov', 204, {})

    def verify_devices_autoprov_called(self, device_id):
        return (
            self.verify_called('GET', f'/devices/{device_id}/autoprov').status_code
            == 202
        )

    def expect_devices_synchronize(self, device_id):
        self.simple_expectation('GET', f'/devices/{device_id}/synchronize', 200, {})

    def verify_devices_synchronize_called(self, device_id):
        return (
            self.verify_called('GET', f'/devices/{device_id}/synchronize').status_code
            == 202
        )

    def expect_lines(self, lines):
        self.simple_expectation('GET', '/lines', 200, lines)

    def verify_lines_called(self):
        return self.verify_called('GET', '/lines').status_code == 202

    def expect_lines_devices(self, line_id, device_id):
        self.simple_expectation('PUT', f'/lines/{line_id}/devices/{device_id}', 200, {})

    def verify_lines_devices_called(self, line_id, device_id):
        return (
            self.verify_called(
                'PUT', f'/lines/{line_id}/devices/{device_id}'
            ).status_code
            == 202
        )

    def expect_groups_get(self, group_id, group):
        self.simple_expectation('GET', f'/groups/{group_id}', 200, group)

    def verify_groups_get_called(self, group_id):
        return self.verify_called('GET', f'/groups/{group_id}').status_code == 202
