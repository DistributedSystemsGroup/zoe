# Copyright (c) 2017, Daniele Venzano
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

"""Interface to PostgresQL for Zoe state."""

import logging

from zoe_lib.state.base import Base

log = logging.getLogger(__name__)


class User(Base):
    """An user object describes a Zoe user."""

    def __init__(self, d, sql_manager):
        super().__init__(d, sql_manager)

        self.username = d['username']
        self.email = d['email']
        self.priority = d['priority']
        self.enabled = d['enabled']
        self._quota_id = d['quota_id']

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'priority': self.priority,
            'enabled': self.enabled,
            'quota_id': self._quota_id
        }

    def set_email(self, new_email: str):
        """Update the email address for this user."""
        self.email = new_email
        self.sql_manager.user_update(self.id, email=new_email)

    def set_priority(self, new_priority: int):
        """Update the priority for this user."""
        self.priority = new_priority
        self.sql_manager.user_update(self.id, priority=new_priority)

    def set_enabled(self, enable: bool):
        """Enable or disable a user."""
        self.enabled = enable
        self.sql_manager.user_update(self.id, enabled=enable)

    @property
    def quota(self):
        """Get the quota for this user."""
        return self.sql_manager.quota_list(only_one=True, id=self._quota_id)

    @quota.setter
    def quota(self, quota_id):
        """Set a different quota for this user."""
        self._quota_id = quota_id
        self.sql_manager.user_update(self.id, quota_id=quota_id)
