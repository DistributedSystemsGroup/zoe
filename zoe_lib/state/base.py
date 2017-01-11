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

"""Interface to PostgresQL for Zoe state."""

import logging

log = logging.getLogger(__name__)


class Base:
    """
    :type sql_manager: SQLManager
    """
    def __init__(self, d, sql_manager):
        """
        :type sql_manager: SQLManager
        """
        self.sql_manager = sql_manager
        self.id = d['id']

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        raise NotImplementedError
