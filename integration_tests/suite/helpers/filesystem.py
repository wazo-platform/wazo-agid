# Copyright 2021-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


class FileSystemClient:
    def __init__(self, execute, service_name=None):
        self.execute = execute
        self.service_name = service_name

    def write_file(self, path, content='content', mode='666', root=False):
        command = ['sh', '-c', f'cat <<EOF > {path}\n{content}\nEOF']
        self.execute(command, service_name=self.service_name)
        self.execute(['cat', path], service_name=self.service_name)
        command = ['chmod', mode, path]
        self.execute(command, service_name=self.service_name)
