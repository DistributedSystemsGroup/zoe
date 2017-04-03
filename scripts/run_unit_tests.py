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

"""Script to run all unit tests with filename `*_test.py` located in folders named `*_tests`."""

import unittest
import glob

UNIT_TEST_FOLDER_PATTERN = "../*_tests"
UNIT_TEST_FILE_PATTERN = "*_test.py"

def _get_all_unit_tests():
    my_suite = unittest.TestLoader().discover(".", pattern=UNIT_TEST_FILE_PATTERN)

    for name in glob.glob(UNIT_TEST_FOLDER_PATTERN):
        my_suite.addTest(unittest.TestLoader().discover(name, pattern=UNIT_TEST_FILE_PATTERN))

    return my_suite


def _run_all_tests(test_suite):
    test_runner = unittest.TextTestRunner()
    test_runner.run(test_suite)


unit_test_suite = _get_all_unit_tests()
_run_all_tests(unit_test_suite)
