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

"""Utility functions used by the Zoe commandline client."""

import os


def read_auth(args):
    """Fill in a dictionary with authentication information."""
    auth = {
        'url': None,
        'user': None,
        'pass': None
    }
    try:
        filep = open(args.auth_file, 'r')
        for line in filep:
            if '=' not in line:
                continue
            key, value = line.split('=')
            key = key.strip()
            value = value.strip()
            if key in auth:
                auth[key] = value
            else:
                print('warning: extraneous value in auth file: {}'.format(line))
    except OSError:
        pass

    auth['url'] = os.getenv('ZOE_URL', auth['url'])
    auth['user'] = os.getenv('ZOE_USER', auth['user'])
    auth['pass'] = os.getenv('ZOE_PASS', auth['pass'])

    for key, value in auth.items():
        if value is None:
            print('error: missing {} auth parameter'.format(key))
            return None

    return auth
