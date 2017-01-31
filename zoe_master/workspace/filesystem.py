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

"""Filesystem implementation for Zoe workspaces."""

import logging
import os.path

import zoe_lib.config as config
from zoe_lib.state import VolumeDescription
import zoe_master.workspace.base

log = logging.getLogger(__name__)


class ZoeFSWorkspace(zoe_master.workspace.base.ZoeWorkspaceBase):
    """Filesystem workspace class."""
    def __init__(self):
        self.base_path = os.path.join(config.get_conf().workspace_base_path, config.get_conf().workspace_deployment_path)

    def exists(self, user_id):
        """Check if the workspace for user_id exists."""
        return os.path.exists(os.path.join(self.base_path, user_id))

    def get_path(self, user_id):
        """Get the volume path of the workspace."""
        return os.path.join(self.base_path, user_id)

    @classmethod
    def can_be_attached(cls):
        """Check if this workspace can be mounted as a Docker volume"""
        return True

    @classmethod
    def get_mountpoint(cls):
        """Get the volume mount point."""
        return '/workspace'

    def get(self, user_id):
        """Return a VolumeDescription for the user workspace."""
        return VolumeDescription((self.get_path(user_id), self.get_mountpoint(), False))
