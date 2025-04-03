# Copyright 2023-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from .mock_clients import MockServerClient


class DirdMockClient(MockServerClient):
    def __init__(self, host, port, version='1.0'):
        super().__init__(host, port, version)

    def expect_reverse_lookup_succeeds(
        self, lookup_extens, user_uuid, display_name
    ):
        graphql_result = {
            'data': {
                'user': {
                    'contacts': {
                        'edges': [
                            {'node': {'wazoReverse': display_name}},
                            {'node': None},
                        ]
                    }
                }
            }
        }
        self.simple_expectation(
            'POST',
            '/graphql',
            200,
            graphql_result,
            body_json_payload={'variables': {'uuid': user_uuid, 'extens': lookup_extens}},
        )

    def expect_reverse_lookup_fails(
        self, lookup_extens, user_uuid
    ):
        graphql_result = {
            'data': {
                'user': {
                    'contacts': {
                        'edges': [
                            {'node': None},
                            {'node': None},
                        ]
                    }
                }
            }
        }
        self.simple_expectation(
            'POST',
            '/graphql',
            200,
            graphql_result,
            body_json_payload={'variables': {'uuid': user_uuid, 'extens': lookup_extens}},
        )
