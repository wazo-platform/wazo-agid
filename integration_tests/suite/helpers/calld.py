from .mock_clients import MockServerClient


class CalldMockClient(MockServerClient):
    def __init__(self, host, port, version='1.0'):
        super().__init__(host, port, version)

    def expect_calls_record_start(self, call_id):
        self.simple_expectation('PUT', f'/calls/{call_id}/record/start', 200, {})

    def verify_calls_record_start_called(self, call_id):
        return (
            self.verify_called('PUT', f'/calls/{call_id}/record/start').status_code
            == 202
        )

    def expect_calls_record_stop(self, call_id):
        self.simple_expectation('PUT', f'/calls/{call_id}/record/stop', 200, {})

    def verify_calls_record_stop_called(self, call_id):
        response = self.verify_called('PUT', f'/calls/{call_id}/record/stop')
        return response.status_code == 202

    def expect_calls_record_pause(self, call_id):
        self.simple_expectation('PUT', f'/calls/{call_id}/record/pause', 200, {})

    def verify_calls_record_pause_called(self, call_id):
        response = self.verify_called('PUT', f'/calls/{call_id}/record/pause')
        return response.status_code == 202

    def expect_calls_record_resume(self, call_id):
        self.simple_expectation('PUT', f'/calls/{call_id}/record/resume', 200, {})

    def verify_calls_record_resume_called(self, call_id):
        response = self.verify_called('PUT', f'/calls/{call_id}/record/resume')
        return response.status_code == 202
