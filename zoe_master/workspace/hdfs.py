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

import zoe_master.platform_manager
import zoe_master.workspace.base
import zoe_master.config as config
import zoe_lib.predefined_apps.hdfs as hdfs_apps
import zoe_master.state.user
import zoe_master.state.application


class ZoeHDFSWorkspace(zoe_master.workspace.base.ZoeWorkspaceBase):
    def __init__(self) -> None:
        self.namenode = config.get_conf().hdfs_namenode
        self.hdfs_docker_network = config.get_conf().hdfs_network
        self.base_path = '/user'

    def create(self, user: zoe_master.state.user.User) -> None:
        path = os.path.join(self.base_path, user.name)
        hdfs_client = hdfs_apps.hdfs_client_app(name='hdfs-mkdir', namenode=self.namenode, user=user.name, command='./mkdir.sh {}'.format(path))
        app = zoe_master.state.application.ApplicationDescription()
        app.from_dict(hdfs_client)
        pm = config.singletons['platform_manager']
        assert isinstance(pm, zoe_master.platform_manager.PlatformManager)
        ex = pm.execution_prepare('hdfs-mkdir', user, app)
        pm.execution_submit(ex)

    def destroy(self, user: zoe_master.state.user.User) -> None:
        path = os.path.join(self.base_path, user.name)
        hdfs_client = hdfs_apps.hdfs_client_app(name='hdfs-rmdir', namenode=self.namenode, user=user.name, command='hdfs dfs -rm -R -skipTrash {}'.format(path))
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
