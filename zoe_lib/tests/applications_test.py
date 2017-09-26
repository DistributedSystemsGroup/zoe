# Copyright (c) 2017, Jordan Kuhn
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

"""Unit tests for zoe_lib/applications.py"""

import json
import pytest

from zoe_lib import applications


class TestApplicationsMethods:
    """Application validation tests."""

    def test_pass_for_zapp(self):
        """Test zapp validation code."""
        zapp_fp = json.load(open('tests/zapp.json', 'r'))
        applications.app_validate(zapp_fp)

    def test_pass_for_complex_zapp(self):
        """Test zapp validation code."""
        zapp_fp = json.load(open('tests/complex_zapp.json', 'r'))
        applications.app_validate(zapp_fp)

    def test_fails_for_zapp(self):
        """Test validation of port number."""
        bad_fp = open('/dev/random', 'r')
        with pytest.raises(applications.InvalidApplicationDescription):
            applications.app_validate(bad_fp)
