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

import time

from zoe_lib.workspace import ZoeWorkspace
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.containers import ZoeContainerAPI
from zoe_lib.info import ZoeInfoAPI


class ZoeWorkFlow:
    def __init__(self, workspace_base_path, identity, name):
        self.identity = identity
        self.name = name
        self.workspace = ZoeWorkspace(workspace_base_path, identity, name)

        self.exec_api = ZoeExecutionsAPI(self.identity['zoe_url'], self.identity['username'], self.identity['password'])
        self.cont_api = ZoeContainerAPI(self.identity['zoe_url'], self.identity['username'], self.identity['password'])

        info_api = ZoeInfoAPI(self.identity['zoe_url'], self.identity['username'], self.identity['password'])
        zoe_info = info_api.info()
        self.hostname_prefix = zoe_info['name_prefix']

    def generate_hostname(self, process_name: str) -> str:
        return self.hostname_prefix + '-' + process_name + '-' + self.identity['username']

    def start_workflow(self):
        self.workspace.create()

    def end_workflow(self):
        self.workspace.destroy()

    def wait_termination(self, exec_id):
        execution = self.exec_api.execution_get(exec_id)
        while execution['status'] == 'submitted' or execution['status'] == 'running':
            time.sleep(1)
            execution = self.exec_api.execution_get(exec_id)

    def __enter__(self):
        self.start_workflow()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_workflow()

