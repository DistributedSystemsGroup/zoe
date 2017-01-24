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

"""LDAP authentication module."""

import logging

try:
    import ldap
    import ldap.sasl
except ImportError:
    ldap = None
    LDAP_AVAILABLE = False
else:
    LDAP_AVAILABLE = True

import zoe_api.auth.base
import zoe_api.exceptions

from zoe_lib.config import get_conf

log = logging.getLogger(__name__)


class LDAPSASLAuthenticator(zoe_api.auth.base.BaseAuthenticator):
    """A simple LDAP authenticator."""

    def __init__(self):
        self.connection = ldap.initialize(get_conf().ldap_server_uri)
        self.base_dn = get_conf().ldap_base_dn
        self.connection.protocol_version = ldap.VERSION3
        self.sasl_auth = ldap.sasl.sasl({}, 'GSSAPI')

    def auth(self, username, password):
        """Authenticate the user or raise an exception."""
        search_filter = "uid=" + username
        uid = None
        role = 'guest'
        try:
            self.connection.sasl_interactive_bind_s('', self.sasl_auth)
            result = self.connection.search_s(self.base_dn, ldap.SCOPE_SUBTREE, search_filter)

            if len(result) == 0:
                raise zoe_api.exceptions.ZoeAuthException('Unknown user or wrong password.')
            user_dict = result[0][1]
            uid = username
            gid_numbers = [int(x) for x in user_dict['gidNumber']]
            if get_conf().ldap_admin_gid in gid_numbers:
                role = 'admin'
            elif get_conf().ldap_user_gid in gid_numbers:
                role = 'user'
            elif get_conf().ldap_guest_gid in gid_numbers:
                role = 'guest'
            else:
                log.warning('User {} has an unknown group ID ({}), using guest role'.format(username, result[0][1]['gidNumber']))
                role = 'guest'
        except ldap.LDAPError as ex:
            if ex.args[0]['desc'] == 'Invalid credentials':
                raise zoe_api.exceptions.ZoeAuthException('Unknown user or wrong password.')
            else:
                log.exception("LDAP exception")
                zoe_api.exceptions.ZoeAuthException('LDAP error.')
        finally:
            self.connection.unbind_s()
        return uid, role
