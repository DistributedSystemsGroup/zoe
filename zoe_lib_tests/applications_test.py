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
    appValidateData = {}
    portCheckData = {}

    def setUp(self):
        currentVersion = version.ZOE_APPLICATION_FORMAT_VERSION
        self.appValidateData = { "name": "test name", "will_end": True, "priority": 3, "requires_binary": False, "version": currentVersion, "services": {} }
        self.portCheckData = { "name": "test name", "protocol": "http", "port_number": 3, "is_main_endpoint": True }

    def test_port_check_works_with_valid_port(self):
        try:
            applications._port_check(self.portCheckData)
        except Exception:
            self.fail("_port_check threw an exception for valid data")

    def test_port_check_fails_for_invalid_port_number(self):
        self.portCheckData["port_number"] = "not_a_number"
        self.assertRaises(applications.InvalidApplicationDescription, applications._port_check, self.portCheckData)

    def test_port_check_fails_for_missing_key(self):
        del self.portCheckData["name"]
        self.assertRaises(applications.InvalidApplicationDescription, applications._port_check, self.portCheckData)

    @patch("zoe_lib.applications._validate_all_services", MagicMock())
    @patch("zoe_lib.applications._port_check", MagicMock())
    def test_app_validate_succeeds_for_valid_app(self):
        applications.app_validate(self.appValidateData)
