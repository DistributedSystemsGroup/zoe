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
        try:
            return func(*args, **kwargs)
        except ZoeRestAPIException as e:
            if e.status_code != 401:
                log.exception(e.message)
            return {'message': e.message}, e.status_code, e.headers
        except ZoeNotFoundException as e:
            return {'message': e.message}, 404
        except ZoeAuthException as e:
            return {'message': e.message}, 401
        except ZoeException as e:
            return {'message': e.message}, 400
        except Exception as e:
            log.exception(str(e))
            return {'message': str(e)}, 500

    return func_wrapper


def get_auth(request):
    """Try to authenticate a request."""
    auth = request.authorization
    if not auth:
        raise ZoeRestAPIException('missing or wrong authentication information', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    authenticator = LDAPAuthenticator()
    uid, role = authenticator.auth(auth.username, auth.password)
    if uid is None:
        raise ZoeRestAPIException('missing or wrong authentication information', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    return uid, role
