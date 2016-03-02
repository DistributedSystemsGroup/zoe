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

from passlib.context import CryptContext

from zoe_scheduler.state.base import BaseState
from zoe_scheduler.config import get_conf


class User(BaseState):
    """
    :type name: str
    :type hashed_password: str
    :type role: list
    :type gateway_docker_id: str
    :type gateway_urls: list
    :type network_id: str
    """

    api_in_attrs = ['name', 'role']
    api_out_attrs = ['name', 'role', 'gateway_urls']
    private_attrs = ['hashed_password', 'gateway_docker_id', 'network_id']

    def __init__(self, state):
        super().__init__(state)

        self.name = ''
        self.hashed_password = ''
        self.role = ''
        self.gateway_docker_id = None
        self.gateway_urls = []
        self.network_id = None

        # Links to other objects
        self.executions = []

        self.pwd_context = CryptContext(schemes=["sha512_crypt"], sha512_crypt__default_rounds=get_conf().passlib_rounds)

    def set_password(self, pw):
        self.hashed_password = self.pwd_context.encrypt(pw)

    def verify_password(self, pw):
        return self.pwd_context.verify(pw, self.hashed_password)

    @property
    def owner(self):
        return self

    def can_see_non_owner_objects(self):
        return self.role == 'admin'

    def set_gateway_urls(self, cont_info):
        socks_url = 'socks://' + cont_info['ports']['1080/tcp'][0] + ':' + cont_info['ports']['1080/tcp'][1]
        self.gateway_urls = [socks_url]
