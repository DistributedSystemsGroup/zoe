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

"""Test module for the API endpoint."""

import pytest

from zoe_api.api_endpoint import APIEndpoint
from zoe_api.tests.mock_master_api import MockAPIManager
from zoe_lib.state.tests.mock_sql_manager import MockSQLManager


class TestAPIEndpoint:
    """The test class."""

    @pytest.fixture(params=[True, False])
    def master_api(self, request):
        """A mock master API manager that can succeed or fail."""
        ret = MockAPIManager()
        ret.fails = request.param
        return ret

    @pytest.fixture
    def sql_manager(self):
        """A mock SQLManager that can succeed or fail."""
        return MockSQLManager()

    def test_statistics_scheduler(self, master_api, sql_manager):
        """Test the scheduler statistics API."""
        api = APIEndpoint(master_api, sql_manager)
        ret = api.statistics_scheduler('nouser', 'norole')
        assert ret == 'No error message' or ret is None
