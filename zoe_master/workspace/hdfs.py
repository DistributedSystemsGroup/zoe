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
import json

import zoe_master.platform_manager
import zoe_master.workspace.base
import zoe_master.config as config
import zoe_master.state.user
import zoe_master.state.application


HDFS_CLIENT_APP = '''
{
    "name": "hdfs-client",
    "priority": 512,
    "requires_binary": false,
    "services": [
        {
            "command": "hdfs dfs -ls /",
            "docker_image": "192.168.45.252:5000/zoerepo/hadoop-client",
            "environment": [],
            "monitor": false,
            "name": "hadoop-client",
            "ports": [],
            "required_resources": {
                "memory": 1073741824
            }
        }
    ],
    "version": 1,
    "will_end": true
}'''


class ZoeHDFSWorkspace(zoe_master.workspace.base.ZoeWorkspaceBase):
    def __init__(self) -> None:
        self.namenode = config.get_conf().hdfs_namenode
        self.hdfs_docker_network = config.get_conf().hdfs_network
        self.base_path = '/user'

    def create(self, user: zoe_master.state.user.User) -> None:
        path = os.path.join(self.base_path, user.name)
        hdfs_client = json.loads(HDFS_CLIENT_APP)
        hdfs_client['name'] = 'hdfs-mkdir'
        hdfs_client['services'][0]['environment'].append(["NAMENODE_HOST", "hdfs-namenode.hdfs"])
        hdfs_client['services'][0]['environment'].append(["HDFS_USER", user.name])
        hdfs_client['services'][0]['command'] = './mkdir.sh {}'.format(path)
        app = zoe_master.state.application.ApplicationDescription()
        app.from_dict(hdfs_client)
        pm = config.singletons['platform_manager']
        assert isinstance(pm, zoe_master.platform_manager.PlatformManager)
        ex = pm.execution_prepare('hdfs-mkdir', user, app)
        pm.execution_submit(ex)

    def destroy(self, user: zoe_master.state.user.User) -> None:
        path = os.path.join(self.base_path, user.name)
        hdfs_client = json.loads(HDFS_CLIENT_APP)
        hdfs_client['name'] = 'hdfs-mkdir'
        hdfs_client['services'][0]['environment'].append(["NAMENODE_HOST", "hdfs-namenode.hdfs"])
        hdfs_client['services'][0]['environment'].append(["HDFS_USER", user.name])
        hdfs_client['services'][0]['command'] = 'hdfs dfs -rm -R -skipTrash {}'.format(path)
        app = zoe_master.state.application.ApplicationDescription()
        app.from_dict(hdfs_client)
        pm = config.singletons['platform_manager']
        assert isinstance(pm, zoe_master.platform_manager.PlatformManager)
        ex = pm.execution_prepare('hdfs-mkdir', user, app)
        pm.execution_submit(ex)

    def exists(self, user):
        return True  # FIXME

    def get_path(self, user: zoe_master.state.user.User) -> str:
        return "hdfs://" + self.namenode + self.base_path + "/" + user.name

    def can_be_attached(self) -> bool:
        return False

    def get_mountpoint(self) -> str:
        return ''
