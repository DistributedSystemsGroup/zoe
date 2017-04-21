# Copyright (c) 2016, Quang-Nhat HOANG-XUAN
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

""" Token generator for oauth2."""

import hashlib
import os
import uuid

class TokenGenerator(object):
    """
    Base class of every token generator.
    """
    def __init__(self):
        """
        Create a new instance of a token generator.
        """
        self.expires_in = {}
        self.refresh_expires_in = 3600

    def create_access_token_data(self, grant_type):
        """
        Create data needed by an access token.

        :param grant_type:
        :type grant_type: str

        :return: A ``dict`` containing he ``access_token`` and the
                 ``token_type``. If the value of ``TokenGenerator.expires_in``
                 is larger than 0, a ``refresh_token`` will be generated too.
        :rtype: dict
        """

        if grant_type == 'password':
            self.expires_in['password'] = 36000

        result = {"access_token": self.generate(), "token_type": "Bearer"}

        if self.expires_in.get(grant_type, 0) > 0:
            result["refresh_token"] = self.generate()

            result["expires_in"] = self.expires_in[grant_type]

        return result

    def generate(self):
        """
        Implemented by generators extending this base class.

        :raises NotImplementedError:
        """
        raise NotImplementedError

class URandomTokenGenerator(TokenGenerator):
    """
    Create a token using ``os.urandom()``.
    """
    def __init__(self, length=40):
        self.token_length = length
        TokenGenerator.__init__(self)

    def generate(self):
        """
        :return: A new token
        :rtype: str
        """
        random_data = os.urandom(100)

        hash_gen = hashlib.new("sha512")
        hash_gen.update(random_data)

        return hash_gen.hexdigest()[:self.token_length]

class Uuid4(TokenGenerator):
    """
    Generate a token using uuid4.
    """
    def generate(self):
        """
        :return: A new token
        :rtype: str
        """
        return str(uuid.uuid4())
