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
import re

from zoe_web.config import get_conf
import zoe_web.master_api
import zoe_lib.sql_manager
import zoe_lib.applications
import zoe_lib.exceptions
import zoe_web.exceptions

log = logging.getLogger(__name__)


class APIEndpoint:
    """
    :type master: zoe_web.master_api.APIManager
    :type sql: zoe_lib.sql_manager.SQLManager
    """
    def __init__(self):
        self.master = zoe_web.master_api.APIManager()
        self.sql = zoe_lib.sql_manager.SQLManager(get_conf())

    def execution_by_id(self, uid, role, execution_id):
        e = self.sql.execution_list(id=execution_id, only_one=True)
        if e is None:
            raise zoe_web.exceptions.ZoeNotFoundException('No such execution')
        if e.user_id != uid and role != 'admin':
            raise zoe_web.exceptions.ZoeAuthException()
        return e

    def execution_list(self, uid, role, **filters):
        execs = self.sql.execution_list(**filters)
        ret = [e for e in execs if e.user_id == uid or role == 'admin']
        return ret

    def execution_start(self, uid, role, exec_name, application_description):
        try:
            zoe_lib.applications.app_validate(application_description)
        except zoe_lib.exceptions.InvalidApplicationDescription as e:
            raise zoe_web.exceptions.ZoeException('Invalid application description: ' + e.message)

        if 3 > len(exec_name) > 128:
            raise zoe_web.exceptions.ZoeException("Execution name must be between 4 and 128 characters long")
        if not re.match(r'^[a-zA-Z0-9\-]+$', exec_name):
            raise zoe_web.exceptions.ZoeException("Execution name can contain only letters, numbers and dashes. '{}' is not valid.".format(exec_name))

        new_id = self.sql.execution_new(exec_name, uid, application_description)
        success, message = self.master.execution_start(new_id)
        if not success:
            raise zoe_web.exceptions.ZoeException(message)
        return new_id

    def execution_terminate(self, uid, role, exec_id):
        e = self.sql.execution_list(id=exec_id, only_one=True)
        if e is None:
            raise zoe_web.exceptions.ZoeNotFoundException('No such execution')

        if e.user_id != uid and role != 'admin':
            raise zoe_web.exceptions.ZoeAuthException()

        if e.is_active():
            return self.master.execution_terminate(exec_id)
        else:
            raise zoe_web.exceptions.ZoeException('Execution is not running')
