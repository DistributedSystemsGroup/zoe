# Copyright (c) 2018, Daniele Venzano
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

"""Main points of entry for the Zoe web interface."""

from zoe_api.web.request_handler import ZoeWebRequestHandler


class UsersEndpointWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self):
        """User admin page."""
        if self.current_user is None or not self.current_user.role.can_change_config:
            return

        template_vars = {
            'kind': 'users',
            'column_keys': ['username', 'email', 'enabled', 'priority', 'fs_uid', 'auth_source', 'role', 'quota'],
            'column_names': ['Username', 'Email', 'Enabled', 'Priority', 'FS UID', 'Authentication', 'Role', 'Quota'],
            'column_types': {
                'username': None,
                'email': 'text',
                'enabled': 'bool',
                'priority': 'number',
                'fs_uid': 'number',
                'auth_source': 'list',
                'role': 'list',
                'quota': 'list'
            },
            'lists': {
                'auth_source': ['internal', 'pam', 'ldap', 'ldap+sasl', 'gitlab-eurecom'],
                'role': self.api_endpoint.role_list(self.current_user),
                'quota': self.api_endpoint.quota_list(self.current_user)
            },
            'rows': self.api_endpoint.user_list(self.current_user)
        }
        self.render('admin.jinja2', **template_vars)

    def post(self):
        """Form submitted."""
        if self.current_user is None or not self.current_user.role.can_change_config:
            return

        user_id = int(self.get_argument('id'))
        if self.get_argument('action') == 'update':
            user_data = {
                'email': None if self.get_argument('email') == '' or self.get_argument('email') == 'None' else self.get_argument('email'),
                'enabled': True if self.get_argument('enabled') == 'on' else False,
                'fs_uid': int(self.get_argument('fs_uid')),
                'auth_source': self.get_argument('auth_source'),
                'role_id': self.api_endpoint.role_by_name(self.get_argument('role')).id,
                'quota_id': self.api_endpoint.quota_by_name(self.get_argument('quota')).id
            }

            self.api_endpoint.user_update(self.current_user, user_id, user_data)
        elif self.get_argument('action') == 'delete':
            self.api_endpoint.user_delete(self.current_user, user_id)
        self.redirect(self.reverse_url('admin_users'))


class RolesEndpointWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self):
        """Roles admin page"""
        if self.current_user is None or not self.current_user.role.can_change_config:
            return

        template_vars = {
            'kind': 'roles',
            'column_keys': ['name', 'can_see_status', 'can_change_config', 'can_operate_others', 'can_delete_executions', 'can_access_api', 'can_customize_resources', 'can_access_full_zapp_shop'],
            'column_names': ['Name', 'See status page', 'Change configuration', 'Operate on non-own executions', 'Delete executions', 'API access', 'Web customize resources', 'Access all ZApps'],
            'column_types': {
                'name': None,
                'can_see_status': 'bool',
                'can_change_config': 'bool',
                'can_operate_others': 'bool',
                'can_delete_executions': 'bool',
                'can_access_api': 'bool',
                'can_customize_resources': 'bool',
                'can_access_full_zapp_shop': 'bool'
            },
            'rows': self.api_endpoint.role_list(self.current_user)
        }
        self.render('admin.jinja2', **template_vars)

    def post(self):
        """Form submitted."""
        if self.current_user is None or not self.current_user.role.can_change_config:
            return


class QuotasEndpointWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self):
        """Quota admin page"""
        if self.current_user is None or not self.current_user.role.can_change_config:
            return

        template_vars = {
            'kind': 'quotas',
            'column_keys': ['name', 'concurrent_executions', 'cores', 'memory', 'runtime_limit'],
            'column_names': ['Name', 'Concurrent executions', 'Cores', 'Memory (GiB)', 'Run time (hours)'],
            'column_types': {
                'name': None,
                'concurrent_executions': 'number',
                'cores': 'number',
                'memory': 'bytes',
                'runtime_limit': 'number'
            },
            'rows': self.api_endpoint.quota_list(self.current_user)
        }
        self.render('admin.jinja2', **template_vars)

    def post(self):
        """Form submitted."""
        if self.current_user is None or not self.current_user.role.can_change_config:
            return
