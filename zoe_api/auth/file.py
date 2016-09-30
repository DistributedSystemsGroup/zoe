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

"""Plain text file authentication module."""

import csv
import logging
import os

import zoe_api.auth.base
import zoe_api.exceptions
from zoe_lib.config import get_conf

log = logging.getLogger(__name__)


class PlainTextAuthenticator(zoe_api.auth.base.BaseAuthenticator):
    """A basic plain text file authenticator."""
    def __init__(self):
        self.passwd_file = get_conf().auth_file
        if not os.access(self.passwd_file, os.R_OK):
            raise zoe_api.exceptions.ZoeNotFoundException('Password file not found at: {}'.format(self.passwd_file))

    def auth(self, username, password):
        """Authenticate the user or raise an exception."""
        with open(self.passwd_file, "r") as passwd:
            passwd_reader = csv.reader(passwd)
            for row in passwd_reader:
                if len(row) != 3:
                    continue
                file_username = row[0]
                file_password = row[1]
                file_role = row[2]
                if file_username == username and file_password == password:
                    return username, file_role
            raise zoe_api.exceptions.ZoeAuthException('Unknown user or password.')
