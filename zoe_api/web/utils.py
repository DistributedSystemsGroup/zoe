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

"""Functions needed by the Zoe web interface."""

import logging

from flask import Response, render_template

from zoe_api.auth.ldap import LDAPAuthenticator
import zoe_api.exceptions

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
        except zoe_api.exceptions.ZoeAuthException:
            return missing_auth()
        except zoe_api.exceptions.ZoeNotFoundException as e:
            return error_page(e.message, 404)
        except zoe_api.exceptions.ZoeException as e:
            return error_page(e, 400)
        except Exception as e:
            log.exception(str(e))
            return {'message': str(e)}, 500

    return func_wrapper


def missing_auth():
    """Sends a 401 response that enables basic auth"""
    return Response('Could not verify your access level for that URL.\nYou have to login with proper credentials',
                    401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def get_auth(request):
    """Try to authenticate a request."""

    auth = request.authorization
    if not auth:
        raise zoe_api.exceptions.ZoeAuthException

    authenticator = LDAPAuthenticator()
    uid, role = authenticator.auth(auth.username, auth.password)
    if uid is None:
        raise zoe_api.exceptions.ZoeAuthException

    return uid, role


def error_page(error_message, status):
    """Generate an error page."""
    return render_template('error.html', error=error_message), status
