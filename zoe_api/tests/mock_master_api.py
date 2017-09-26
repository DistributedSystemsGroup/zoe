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

"""Mock master API for unit testing."""

import logging
from typing import Tuple

log = logging.getLogger(__name__)

APIReturnType = Tuple[bool, str]


class MockAPIManager:
    """Main class for the API."""

    def __init__(self):
        self.fails = False

    def _request_reply(self) -> APIReturnType:
        """
        Fake connection.
        """
        if not self.fails:
            return True, 'No error message'
        else:
            return False, 'Fake error message'

    def execution_start(self, exec_id: int) -> APIReturnType:
        """Start an execution."""
        assert isinstance(exec_id, int)
        return self._request_reply()

    def execution_terminate(self, exec_id: int) -> APIReturnType:
        """Terminate an execution."""
        assert isinstance(exec_id, int)
        return self._request_reply()

    def execution_delete(self, exec_id: int) -> APIReturnType:
        """Delete an execution."""
        assert isinstance(exec_id, int)
        return self._request_reply()

    def scheduler_statistics(self) -> APIReturnType:
        """Query scheduler statistics."""
        return self._request_reply()
