# Copyright (c) 2016, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil


class ZoeWorkspace:
    def __init__(self, base_path, identity, wk_name):
        self._workspace_name = identity['username'] + '-' + wk_name
        self._workspace_path = os.path.join(base_path, self._workspace_name)
        self._workspace_volume = {
            'host_path': self._workspace_path,
            'cont_path': '/mnt/workspace',
            'readonly': False
        }

    def create(self):
        print("Creating workspace {}".format(self._workspace_path))
        os.makedirs(self._workspace_path, exist_ok=False)

    def destroy(self):
        print("Destroying workspace {}".format(self._workspace_path))
        shutil.rmtree(self._workspace_path)

    def get_volume_definition(self):
        return self._workspace_volume

    def put(self, src_filepath, dst_rel_filepath):
        dst_path = os.path.join(self._workspace_path, dst_rel_filepath)
        print("Copying file {} to {}".format(src_filepath, dst_path))
        shutil.copyfile(src_filepath, dst_path)

    def put_string(self, file_contents, dst_rel_filepath):
        dst_path = os.path.join(self._workspace_path, dst_rel_filepath)
        open(dst_path, 'wb').write(file_contents.encode('utf-8'))

    def chmod(self, rel_path: str, octal_perms: int):
        dst_path = os.path.join(self._workspace_path, rel_path)
        os.chmod(dst_path, octal_perms)
