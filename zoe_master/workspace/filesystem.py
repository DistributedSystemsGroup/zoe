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

import os.path
import shutil

import zoe_master.workspace.base
import zoe_master.config as config


class ZoeFSWorkspace(zoe_master.workspace.base.ZoeWorkspaceBase):
    def __init__(self):
        self.base_path = os.path.join(config.get_conf().workspace_base_path, config.get_conf().deployment_name)

    def create(self, user):
        path = os.path.join(self.base_path, user.name)
        os.makedirs(path, exist_ok=True)

    def destroy(self, user):
        path = os.path.join(self.base_path, user.name)
        shutil.rmtree(path)

    def exists(self, user):
        return os.path.exists(os.path.join(self.base_path, user.name))

    def get_path(self, user):
        return os.path.join(self.base_path, user.name)

    def can_be_attached(self):
        return True

    def get_mountpoint(self):
        return '/mnt/workspace'
