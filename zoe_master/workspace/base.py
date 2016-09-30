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

"""Base implementation for Zoe workspaces."""


class ZoeWorkspaceBase:
    """Workspace base class."""
    def get_path(self, user_id) -> str:
        """Check if the workspace for user_id exists."""
        raise NotImplementedError

    def exists(self, user_id) -> bool:
        """Get the volume path of the workspace."""
        raise NotImplementedError

    def can_be_attached(self) -> bool:
        """Check if this workspace can be mounted as a Docker volume"""
        raise NotImplementedError

    def get_mountpoint(self) -> str:
        """Get the volume mount point."""
        raise NotImplementedError
