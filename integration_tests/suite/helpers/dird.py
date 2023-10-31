from .mock_clients import MockServerClient


class DirdMockClient(MockServerClient):
    def __init__(self, host, port, version='1.0'):
        super().__init__(host, port, version)

    def expect_reverse_lookup_succeeds(
        self, lookup_term, user_uuid, display_name, fields
    ):
        self.simple_expectation(
            'GET',
            f'/directories/reverse/default/{user_uuid}',
            200,
            {'display': display_name, 'fields': fields},
            query_string_params={'exten': [lookup_term]},
        )
