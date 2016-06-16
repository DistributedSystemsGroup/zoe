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
import logging

import ldap

import zoe_web.auth.base
from zoe_web.config import get_conf

log = logging.getLogger(__name__)


class LDAPAuthenticator(zoe_web.auth.base.BaseAuthenticator):
    def __init__(self):
        self.connection = ldap.initialize(get_conf().ldap_server_uri)
        self.base_dn = get_conf().ldap_base_dn
        self.bind_user = get_conf().ldap_bind_user
        self.bind_password = get_conf().ldap_bind_password

    def auth(self, username, password):
        search_filter = "uid=" + username
        uid_number = None
        role = 'guest'
        try:
            self.connection.bind_s(self.bind_user, self.bind_password)
            result = self.connection.search_s(self.base_dn, ldap.SCOPE_SUBTREE, search_filter)
            user_dict = result[0][1]
            uid_number = int(user_dict['uidNumber'][0])
            gid_numbers = [int(x) for x in user_dict['gidNumber']]
            if get_conf().ldap_admin_gid in gid_numbers:
                role = 'admin'
            elif get_conf().ldap_user_gid in gid_numbers:
                role = 'user'
            elif get_conf().ldap_guest_gid in gid_numbers:
                role = 'guest'
            else:
                log.warn('User {} has an unknown group ID ({}), using guest role'.format(username, result[0][1]['gidNumber']))
                role = 'guest'
        except ldap.LDAPError:
            log.exception("LDAP exception")
        finally:
            self.connection.unbind_s()
        return uid_number, role
