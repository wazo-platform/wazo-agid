# Copyright 2023-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import requests


class MockServerClient:
    def __init__(self, host, port, version):
        self.host = host
        self.port = port
        self.version = version
        self._url = f'http://{host}:{port}'

    def simple_expectation(
        self,
        method,
        path,
        expected_status,
        expected_body,
        headers=None,
        query_string_params=None,
        body_json_payload=None,
        response_headers=None,
        request_headers=None,
    ):
        expectation = {
            'httpRequest': {
                'method': method,
                'path': f'/{self.version}{path}',
            },
            'httpResponse': {
                'statusCode': expected_status,
                'body': expected_body,
            },
        }
        if query_string_params:
            expectation['httpRequest']['queryStringParameters'] = query_string_params
        if body_json_payload:
            expectation['httpRequest']['body'] = body_json_payload
        if request_headers:
            expectation['httpRequest']['headers'] = request_headers
        if response_headers:
            expectation['httpResponse']['headers'] = response_headers
        expectation_kwargs = {}
        if headers:
            expectation_kwargs['headers'] = headers
        return self.expectation(expectation, **expectation_kwargs)

    def expectation(self, expectation, **kwargs):
        return requests.put(f'{self._url}/expectation', json=expectation, **kwargs)

    def reset(self):
        return requests.put(f'{self._url}/reset')

    def clear(self):
        return requests.put(f'{self._url}/clear')

    def verify_called(self, method, path, times_called=1, **kwargs):
        verification = {
            'httpRequest': {
                'method': method,
                'path': f'/{self.version}{path}',
            },
            'times': {
                'atLeast': times_called,
                'atMost': times_called,
            },
        }
        verification.update(kwargs)
        return requests.put(f'{self._url}/verify', json=verification)

    def is_up(self):
        try:
            response = requests.get(self._url)
            return response.status_code == 404
        except requests.RequestException:
            return False
