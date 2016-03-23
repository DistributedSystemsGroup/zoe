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

from zoe_master.workspace import ZoeWorkspaceBase
from zoe_master.config import get_conf


class ZoeFSWorkspace(ZoeWorkspaceBase):
    def __init__(self):
        self.base_path = get_conf().workspace_base_path

    def create(self, user):
        path = os.path.join(self.base_path, user.name)
        os.makedirs(path, exist_ok=False)

    def destroy(self, user):
        path = os.path.join(self.base_path, user.name)
        shutil.rmtree(path)

    def get_path(self, user):
        return os.path.join(self.base_path, user.name)

    def can_be_attached(self):
        return True
