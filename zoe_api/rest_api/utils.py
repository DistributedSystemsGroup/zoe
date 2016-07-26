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

"""Utility functions needed by the Zoe REST API."""

import base64
import logging

from zoe_api.exceptions import ZoeRestAPIException, ZoeNotFoundException, ZoeAuthException, ZoeException
from zoe_api.auth.ldap import LDAPAuthenticator

log = logging.getLogger(__name__)


def catch_exceptions(func):
    """
    Decorator function used to work around the static exception system available in Flask-RESTful
    :param func:
    :return:
    """
    def func_wrapper(*args, **kwargs):
        """The actual decorator."""
        self = args[0]
        try:
            return func(*args, **kwargs)
        except ZoeRestAPIException as e:
            if e.status_code != 401:
                log.exception(e.message)
            self.set_status(e.status_code)
            for key, value in e.headers.items():
                self.set_header(key, value)
            self.write({'message': e.message})
        except ZoeNotFoundException as e:
            self.set_status(404)
            self.write({'message': e.message})
        except ZoeAuthException as e:
            self.set_status(401)
            self.write({'message': e.message})
        except ZoeException as e:
            self.set_status(400)
            self.write({'message': e.message})
        except Exception as e:
            self.set_status(500)
            log.exception(str(e))
            self.write({'message': str(e)})

    return func_wrapper


def get_auth(request):
    """Try to authenticate a request."""
    auth_header = request.request.headers.get('Authorization')
    if auth_header is None or not auth_header.startswith('Basic '):
        raise ZoeRestAPIException('missing or wrong authentication information', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    auth_decoded = base64.decodebytes(bytes(auth_header[6:], 'ascii')).decode('utf-8')
    username, password = auth_decoded.split(':', 2)

    authenticator = LDAPAuthenticator()
    uid, role = authenticator.auth(username, password)
    if uid is None:
        raise ZoeRestAPIException('missing or wrong authentication information', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    return uid, role
