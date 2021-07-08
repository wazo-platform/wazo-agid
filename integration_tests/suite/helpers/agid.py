# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import re
import socket
from contextlib import contextmanager

GET_VARIABLE_REGEX = r'^GET VARIABLE "(.*)"$'
SET_VARIABLE_REGEX = r'^SET VARIABLE "(.*)" "(.*)"$'
CMD_STATUS_REGEX = r'^Status: OK$'
CMD_VERBOSE_REGEX = r'^VERBOSE "(.*)" (\d)$'
CMD_GENERIC_REGEX = r'^(.*) "(.*)"'


class AgidClient:
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._socket = None

    def monitoring(self):
        with self._connect():
            self._send_handler('monitoring')
            variables, commands = self._process_communicate()
        return variables, commands

    def incoming_user_set_features(self, variables):
        with self._connect():
            self._send_handler('incoming_user_set_features')
            variables, commands = self._process_communicate(variables)
        return variables, commands

    @contextmanager
    def _connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            self._socket = s
            self._socket.connect((self._host, self._port))
            yield
            self._socket.close()
            self._socket = None

    def _send_handler(self, command):
        self._send_fragment('agi_network: yes')
        self._send_fragment(f'agi_network_script: {command}')
        fragment = f'agi_request: agi://localhost/{command}'
        self._send_fragment(fragment)
        self._send_fragment('')

    def _send_result(self, result=1, data=None):
        message = f'200 result={result}'
        if data:
            message = f'200 result={result} ({data})'
        self._send_fragment(message)

    def _send_fragment(self, fragment):
        fragment = fragment + '\n'
        fragment = fragment.encode('utf-8')
        self._socket.send(fragment)

    def _process_communicate(self, variables=None):
        received_variables = {}
        received_commands = {'VERBOSE': []}
        while True:
            data = self._socket.recv(1024).decode('utf-8')
            if not data:
                break

            result = re.search(GET_VARIABLE_REGEX, data)
            if result:
                name = result.group(1)
                self._send_result(data=variables[name])
                continue

            result = re.search(SET_VARIABLE_REGEX, data)
            if result:
                name = result.group(1)
                value = result.group(2)
                self._send_result()
                received_variables[name] = value
                continue

            result = re.search(CMD_STATUS_REGEX, data)
            if result:
                self._send_result()
                received_commands['Status'] = 'OK'
                continue

            result = re.search(CMD_VERBOSE_REGEX, data)
            if result:
                message = result.group(1)
                # code = result.group(2)
                self._send_result()
                received_commands['VERBOSE'].append(message)
                continue

            result = re.search(CMD_GENERIC_REGEX, data)
            if result:
                command = result.group(1)
                arg = result.group(2)
                self._send_result()
                received_commands[command] = arg
                continue
            return received_variables, received_commands

            raise Exception(data)

        return received_variables, received_commands
