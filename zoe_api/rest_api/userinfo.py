# Copyright (c) 2016, Quang-Nhat Hoang-Xuan
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

"""The User Info API endpoint."""

from zoe_api.rest_api.request_handler import ZoeAPIRequestHandler


class UserInfoAPI(ZoeAPIRequestHandler):
    """The UserInfo API endpoint."""

    def get(self):
        """HTTP GET method."""
        if self.current_user is None:
            return

        ret = {
            'user': self.current_user
        }

        self.write(ret)
