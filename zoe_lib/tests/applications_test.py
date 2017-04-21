#!/usr/bin/env python3

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

import unittest
from unittest.mock import patch, MagicMock

from zoe_lib import applications
from zoe_lib import version


class TestApplicationsMethods(unittest.TestCase):
    """Application validation tests."""
    app_validate_data = {}
    port_check_data = {}

    def setUp(self):
        """Set up tests."""
        current_version = version.ZOE_APPLICATION_FORMAT_VERSION
        self.app_validate_data = {
            "name": "test name",
            "will_end": True,
            "priority": 3,
            "requires_binary": False,
            "version": current_version,
            "services": []
        }
        self.port_check_data = {
            "name": "test name",
            "protocol": "http",
            "port_number": 3,
            "is_main_endpoint": True
        }

    def test_pass_for_valid_port(self):
        """Test port validation code."""
        try:
            applications._port_check(self.port_check_data)  # pylint: disable=protected-access
        except Exception:
            self.fail("_port_check threw an exception for valid data")

    def test_fails_for_bad_port_number(self):
        """Test validation of port number."""
        self.port_check_data["port_number"] = "not_a_number"
        self.assertRaises(applications.InvalidApplicationDescription, applications._port_check, self.port_check_data)  # pylint: disable=protected-access

    def test_fails_for_missing_key(self):
        """Test missing name key from the port definition."""
        del self.port_check_data["name"]
        self.assertRaises(applications.InvalidApplicationDescription, applications._port_check, self.port_check_data)  # pylint: disable=protected-access

    @patch("zoe_lib.applications._validate_all_services", MagicMock())
    @patch("zoe_lib.applications._port_check", MagicMock())
    def test_pass_for_valid_app(self):
        """Test validation of entire app."""
        applications.app_validate(self.app_validate_data)
