# Copyright 2021-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from functools import partial


class FileSystemClient:
    def __init__(self, execute, service_name=None):
        self.execute = partial(execute, service_name=service_name)

    def write_file(self, path, content='content', mode='666', chown=None):
        command = ['sh', '-c', f'cat <<EOF > {path}\n{content}\nEOF']
        self.execute(command)
        self.execute(['cat', path])
        command = ['chmod', mode, path]
        self.execute(command)
        if chown:
            self.execute(['chown', chown, path])

    def create_path(self, path, mode='666', chown=None):
        self.execute(['mkdir', '-p', path])
        self.execute(['chmod', '-R', mode, path])
        if chown:
            self.execute(['chown', '-R', chown, path])

    def find_file(self, path, pattern):
        cmd = ['find', path, '-maxdepth', '1', '-name', pattern, '-print', '-quit']
        return self.execute(cmd).decode('utf8').strip('\n')

    def read_file(self, path):
        return self.execute(['cat', path]).decode('utf8')
