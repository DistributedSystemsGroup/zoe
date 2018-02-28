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

"""The real API, exposed as web pages or REST API."""

import logging
import os
from typing import List

import zoe_api.exceptions
import zoe_api.master_api
import zoe_lib.applications
import zoe_lib.exceptions
import zoe_lib.state
from zoe_lib.config import get_conf

log = logging.getLogger(__name__)


class APIEndpoint:
    """
    The APIEndpoint class.

    :type master: zoe_api.master_api.APIManager
    :type sql: zoe_lib.sql_manager.SQLManager
    """
    def __init__(self, master_api, sql_manager: zoe_lib.state.SQLManager):
        self.master = master_api
        self.sql = sql_manager

    def execution_by_id(self, user: zoe_lib.state.User, execution_id: int) -> zoe_lib.state.Execution:
        """Lookup an execution by its ID."""
        e = self.sql.executions.select(id=execution_id, only_one=True)
        if e is None:
            raise zoe_api.exceptions.ZoeNotFoundException('No such execution')
        assert isinstance(e, zoe_lib.state.Execution)
        if e.user_id != user.id and not user.role.can_operate_others:
            raise zoe_api.exceptions.ZoeAuthException()
        return e

    def execution_list(self, user: zoe_lib.state.User, **filters):
        """Generate a optionally filtered list of executions."""
        if not user.role.can_operate_others:
            filters['user_id'] = user.id
        execs = self.sql.executions.select(**filters)
        return execs

    def execution_count(self, user: zoe_lib.state.User, **filters):
        """Count the number of executions optionally filtered."""
        if not user.role.can_operate_others:
            filters['user_id'] = user.id
        return self.sql.executions.count(**filters)

    def zapp_validate(self, application_description):
        """Validates the passed ZApp description against the supported schema."""
        try:
            zoe_lib.applications.app_validate(application_description)
        except zoe_lib.exceptions.InvalidApplicationDescription as e:
            raise zoe_api.exceptions.ZoeRestAPIException('Invalid application description: ' + e.message)

    def _check_quota(self, user: zoe_lib.state.User, application_description):  # pylint: disable=unused-argument
        """Check quota for given user and execution."""
        quota = self.sql.quota.select(only_one=True, **{'id': user.quota_id})

        running_execs = self.sql.executions.select(**{'status': 'running', 'user_id': user.id})
        running_execs += self.sql.executions.select(**{'status': 'starting', 'user_id': user.id})
        running_execs += self.sql.executions.select(**{'status': 'scheduled', 'user_id': user.id})
        running_execs += self.sql.executions.select(**{'status': 'image download', 'user_id': user.id})
        running_execs += self.sql.executions.select(**{'status': 'submitted', 'user_id': user.id})
        if len(running_execs) >= quota.concurrent_executions:
            raise zoe_api.exceptions.ZoeQuotaException('You cannot run more than {} executions at a time, quota exceeded.'.format(quota.concurrent_executions))

        # TODO: implement core and memory quotas

    def execution_start(self, user: zoe_lib.state.User, exec_name, application_description):
        """Start an execution."""
        try:
            zoe_lib.applications.app_validate(application_description)
        except zoe_lib.exceptions.InvalidApplicationDescription as e:
            raise zoe_api.exceptions.ZoeRestAPIException('Invalid application description: ' + e.message)

        self._check_quota(user, application_description)

        new_id = self.sql.executions.insert(exec_name, user.id, application_description)
        success, message = self.master.execution_start(new_id)
        if not success:
            raise zoe_api.exceptions.ZoeRestAPIException('The Zoe master is unavailable, execution will be submitted automatically when the master is back up ({}).'.format(message), status_code=503)

        return new_id

    def execution_terminate(self, user: zoe_lib.state.User, exec_id: int):
        """Terminate an execution."""
        e = self.sql.executions.select(id=exec_id, only_one=True)
        assert isinstance(e, zoe_lib.state.Execution)
        if e is None:
            raise zoe_api.exceptions.ZoeNotFoundException('No such execution')

        if e.user_id != user.id and not user.role.can_operate_others:
            raise zoe_api.exceptions.ZoeAuthException('You are not authorized to terminate this execution')

        if e.is_active:
            success, message = self.master.execution_terminate(exec_id)
            if not success:
                raise zoe_api.exceptions.ZoeRestAPIException(message)
        else:
            raise zoe_api.exceptions.ZoeRestAPIException('Execution is not running')

    def execution_delete(self, user: zoe_lib.state.User, exec_id: int):
        """Delete an execution."""
        if not user.role.can_delete_executions:
            raise zoe_api.exceptions.ZoeAuthException()

        e = self.sql.executions.select(id=exec_id, only_one=True)
        assert isinstance(e, zoe_lib.state.Execution)
        if e is None:
            raise zoe_api.exceptions.ZoeNotFoundException('No such execution')

        if e.user_id != user.id and not user.role.can_operate_others:
            raise zoe_api.exceptions.ZoeAuthException('You are not authorized to terminate this execution')

        if e.is_active:
            raise zoe_api.exceptions.ZoeRestAPIException('Cannot delete an active execution')

        status, message = self.master.execution_delete(exec_id)
        if status:
            self.sql.executions.delete(exec_id)
        else:
            raise zoe_api.exceptions.ZoeRestAPIException(message)

    def service_by_id(self, user: zoe_lib.state.User, service_id: int) -> zoe_lib.state.Service:
        """Lookup a service by its ID."""
        service = self.sql.services.select(id=service_id, only_one=True)
        if service is None:
            raise zoe_api.exceptions.ZoeNotFoundException('No such execution')
        if service.user_id != user.id and not user.role.can_operate_others:
            raise zoe_api.exceptions.ZoeAuthException()
        return service

    def service_list(self, user: zoe_lib.state.User, **filters):
        """Generate a optionally filtered list of services."""
        if not user.role.can_operate_others:
            filters['user_id'] = user.id
        return self.sql.services.select(**filters)

    def service_logs(self, user: zoe_lib.state.User, service_id):
        """Retrieve the logs for the given service.
        If stream is True, a file object is returned, otherwise the log contents as a str object.
        """
        service = self.sql.services.select(id=service_id, only_one=True)
        if service is None:
            raise zoe_api.exceptions.ZoeNotFoundException('No such service')
        if service.user_id != user.id and not user.role.can_operate_others:
            raise zoe_api.exceptions.ZoeAuthException()

        path = os.path.join(get_conf().service_logs_base_path, get_conf().deployment_name, str(service.execution_id), service.name + '.txt')
        if not os.path.exists(path):
            raise zoe_api.exceptions.ZoeNotFoundException('Service log not available')
        return open(path, encoding='utf-8')

    def statistics_scheduler(self):
        """Retrieve statistics about the scheduler."""
        success, message = self.master.scheduler_statistics()
        if success:
            for node in message['platform_stats']['nodes']:  # JSON does not like hash keys to be integers, so we need to convert manually
                for str_service_id in list(node['service_stats'].keys()):
                    node['service_stats'][int(str_service_id)] = node['service_stats'][str_service_id]
                    del node['service_stats'][str_service_id]
            return message
        else:
            raise zoe_api.exceptions.ZoeException(message=message)

    def execution_endpoints(self, user: zoe_lib.state.User, execution: zoe_lib.state.Execution):
        """Return a list of the services and public endpoints available for a certain execution."""
        services_info = []
        endpoints = []
        for service in execution.services:
            services_info.append(self.service_by_id(user, service.id))
            for port in service.description['ports']:
                port_key = str(port['port_number']) + "/" + port['protocol']
                backend_port = self.sql.ports.select(only_one=True, service_id=service.id, internal_name=port_key)
                if backend_port is not None and backend_port.external_ip is not None:
                    endpoint = port['url_template'].format(**{"ip_port": backend_port.external_ip + ":" + str(backend_port.external_port)})
                    endpoints.append((port['name'], endpoint))

        return services_info, endpoints

    def user_by_name(self, username) -> zoe_lib.state.User:
        """Finds a user in the database looking it up by its username."""
        return self.sql.user.select(only_one=True, **{'username': username})

    def user_by_id(self, user: zoe_lib.state.User, user_id: int) -> zoe_lib.state.User:
        """Finds a user in the database looking it up by its username."""
        if user.id == user_id:
            return user
        if not user.role.can_change_config:
            raise zoe_api.exceptions.ZoeAuthException()

        ret = self.sql.user.select(only_one=True, id=user_id)
        if ret is None:
            raise zoe_api.exceptions.ZoeNotFoundException("No such user")
        else:
            return ret

    def user_delete(self, user: zoe_lib.state.User, user_id: int):
        """Deletes the user identified by the ID."""
        if not user.role.can_change_config:
            raise zoe_api.exceptions.ZoeAuthException()

        user_to_del = self.user_by_id(user, user_id)
        if user_to_del.username == "admin":
            raise zoe_api.exceptions.ZoeRestAPIException('The admin user cannot be deleted, but it can be disabled')

        self.sql.user.delete(user_id)

    def user_list(self, user: zoe_lib.state.User, **filters) -> List[zoe_lib.state.User]:
        """Generate a optionally filtered list of users."""
        if not user.role.can_change_config:
            raise zoe_api.exceptions.ZoeAuthException()
        users = self.sql.user.select(**filters)
        return users

    def user_new(self, user: zoe_lib.state.User, username: str, email: str, role_id: int, quota_id: int, auth_source: str) -> int:
        """Creates a new user."""
        if not user.role.can_change_config:
            raise zoe_api.exceptions.ZoeAuthException()

        if self.role_by_id(role_id) is None:
            raise zoe_api.exceptions.ZoeNotFoundException("Role {} does not exist".format(role_id))
        if self.quota_by_id(quota_id) is None:
            raise zoe_api.exceptions.ZoeNotFoundException("Quota {} does not exist".format(quota_id))

        return self.sql.user.insert(username, email, auth_source, role_id, quota_id)

    def user_update(self, user: zoe_lib.state.User, user_id, user_data):
        """Update a user."""

        self.user_by_id(user, user_id)

        update_fields = {}

        if not user.role.can_change_config:
            if 'email' in user_data:
                update_fields['email'] = user_data['email']
        else:
            if 'email' in user_data:
                update_fields['email'] = user_data['email']
            if 'priority' in user_data:
                update_fields['priority'] = user_data['priority']
            if 'enabled' in user_data:
                update_fields['enabled'] = user_data['enabled']
            if 'auth_source' in user_data:
                update_fields['auth_source'] = user_data['auth_source']
                if user_data['auth_source'] != 'internal':
                    user_data['password'] = None
            if 'quota_id' in user_data:
                quota = self.quota_by_id(user_data['quota_id'])
                if quota is None:
                    raise zoe_api.exceptions.ZoeRestAPIException('No quota with ID {}'.format(user_data['quota_id']))
                update_fields['quota_id'] = quota.id
            if 'role' in user_data:
                role = self.role_by_id(user_data['role_id'])
                if role is None:
                    raise zoe_api.exceptions.ZoeRestAPIException('No role with ID {}'.format(user_data['role_id']))
                update_fields['role_id'] = role.id
            if 'password' in user_data:
                update_fields['password'] = user_data['password']
                update_fields['auth_source'] = 'internal'

        self.sql.user.update(user_id, **update_fields)

    def quota_by_name(self, quota) -> zoe_lib.state.Quota:
        """Finds a quota in the database looking it up by its name."""
        return self.sql.quota.select(only_one=True, **{'name': quota})

    def quota_by_id(self, quota_id) -> zoe_lib.state.Quota:
        """Finds a quota in the database looking it up by its id."""
        quota = self.sql.quota.select(only_one=True, **{'id': quota_id})
        if quota is None:
            raise zoe_api.exceptions.ZoeNotFoundException('No such quota')
        else:
            return quota

    def role_by_name(self, role) -> zoe_lib.state.Role:
        """Finds a role in the database looking it up by its name."""
        return self.sql.role.select(only_one=True, **{'name': role})

    def role_by_id(self, role_id) -> zoe_lib.state.Role:
        """Finds a role in the database looking it up by its id."""
        role = self.sql.role.select(only_one=True, **{'id': role_id})
        if role is None:
            raise zoe_api.exceptions.ZoeNotFoundException('No such role')
        else:
            return role

    def role_new(self, user: zoe_lib.state.User, role_data) -> int:
        """Creates a new role."""
        if not user.role.can_change_config:
            raise zoe_api.exceptions.ZoeAuthException()

        role_id = self.sql.role.insert(role_data['name'])
        self.sql.role.update(role_id, **role_data)
        return role_id

    def role_list(self, user: zoe_lib.state.User, **filters) -> List[zoe_lib.state.Role]:
        """Generate a optionally filtered list of roles."""
        if not user.role.can_change_config:
            raise zoe_api.exceptions.ZoeAuthException()
        users = self.sql.role.select(**filters)
        return users

    def role_delete(self, user: zoe_lib.state.User, role_id: int):
        """Deletes the role identified by the ID."""
        if not user.role.can_change_config:
            raise zoe_api.exceptions.ZoeAuthException()

        role = self.role_by_id(role_id)
        if role.name == "admin":
            raise zoe_api.exceptions.ZoeRestAPIException('Cannot delete admin role')

        self.sql.role.delete(role_id)

    def role_update(self, user: zoe_lib.state.User, role_id: int, role_data):
        """Update a role."""
        if not user.role.can_change_config:
            raise zoe_api.exceptions.ZoeAuthException()

        role = self.role_by_id(role_id)

        if role.name == "admin":
            raise zoe_api.exceptions.ZoeRestAPIException('Cannot edit the admin role')

        self.sql.role.update(role_id, **role_data)

    def quota_new(self, user: zoe_lib.state.User, quota_data) -> int:
        """Creates a new quota."""
        if not user.role.can_change_config:
            raise zoe_api.exceptions.ZoeAuthException()

        role_id = self.sql.quota.insert(quota_data['name'], quota_data['concurrent_executions'], quota_data['memory'], quota_data['cores'])
        return role_id

    def quota_list(self, user: zoe_lib.state.User, **filters) -> List[zoe_lib.state.Quota]:
        """Generate a optionally filtered list of quotas."""
        if not user.role.can_change_config:
            raise zoe_api.exceptions.ZoeAuthException()
        users = self.sql.quota.select(**filters)
        return users

    def quota_delete(self, user: zoe_lib.state.User, quota_id: int):
        """Deletes the quota identified by the ID."""
        if not user.role.can_change_config:
            raise zoe_api.exceptions.ZoeAuthException()

        quota = self.quota_by_id(quota_id)
        if quota is None:
            raise zoe_api.exceptions.ZoeNotFoundException('No such quota')
        if quota.name == "default":
            raise zoe_api.exceptions.ZoeRestAPIException('Cannot delete default quota')

        self.sql.quota.delete(quota_id)

    def quota_update(self, user: zoe_lib.state.User, quota_id, quota_data):
        """Update a quota."""
        if not user.role.can_change_config:
            raise zoe_api.exceptions.ZoeAuthException()

        quota = self.quota_by_id(quota_id)
        if quota.name == "default" and "name" in quota_data:
            raise zoe_api.exceptions.ZoeRestAPIException('Cannot rename default quota')

        self.sql.quota.update(quota_id, **quota_data)
