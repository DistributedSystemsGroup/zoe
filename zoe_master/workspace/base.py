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

import zoe_master.state.user


class ZoeWorkspaceBase:
    def create(self, user: zoe_master.state.user.User):
        raise NotImplementedError

    def destroy(self, user: zoe_master.state.user.User):
        raise NotImplementedError

    def get_path(self, user: zoe_master.state.user.User) -> str:
        raise NotImplementedError

    def exists(self, user: zoe_master.state.user.User) -> bool:
        raise NotImplementedError

    def can_be_attached(self) -> bool:
        raise NotImplementedError

    def get_mountpoint(self) -> str:
        raise NotImplementedError
