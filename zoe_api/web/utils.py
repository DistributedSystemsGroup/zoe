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

from zoe_lib.config import get_conf

from zoe_api.auth.base import BaseAuthenticator  # pylint: disable=unused-import
from zoe_api.auth.ldap import LDAPAuthenticator
from zoe_api.auth.ldapsasl import LDAPSASLAuthenticator
from zoe_api.auth.file import PlainTextAuthenticator
import zoe_api.exceptions
from zoe_api.web.custom_request_handler import ZoeRequestHandler

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
        except zoe_api.exceptions.ZoeAuthException:
            return missing_auth(self)
        except zoe_api.exceptions.ZoeNotFoundException as e:
            return error_page(self, str(e), 404)
        except zoe_api.exceptions.ZoeException as e:
            return error_page(self, str(e), 400)
        except Exception as e:
            log.exception(str(e))
            return {'message': str(e)}, 500

    return func_wrapper


def missing_auth(handler: ZoeRequestHandler):
    """Redirect to login page."""
    handler.redirect(handler.get_argument('next', u'/login'))


def get_auth_login(username, password):
    """Authenticate username and password against the configured user store."""
    if get_conf().auth_type == 'text':
        authenticator = PlainTextAuthenticator()  # type: BaseAuthenticator
    elif get_conf().auth_type == 'ldap':
        authenticator = LDAPAuthenticator()  # type: BaseAuthenticator
    elif get_conf().auth_type == 'ldapsasl':
        authenticator = LDAPSASLAuthenticator()  # type: BaseAuthenticator
    else:
        raise zoe_api.exceptions.ZoeException('Configuration error, unknown authentication method: {}'.format(get_conf().auth_type))
    uid, role = authenticator.auth(username, password)
    if uid is None:
        raise zoe_api.exceptions.ZoeAuthException

    return uid, role


def get_auth(handler: ZoeRequestHandler):
    """Try to authenticate a request."""

    if handler.get_secure_cookie('zoe'):
        cookie_val = str(handler.get_secure_cookie('zoe'))
        uid, role = cookie_val[2:-1].split('.')
        log.info('Authentication done using cookie')
        return uid, role
    else:
        handler.redirect(handler.get_argument('next', u'/login'))


def error_page(handler: ZoeRequestHandler, error_message: str, status: int):
    """Generate an error page."""
    handler.set_status(status)
    handler.render('error.html', error=error_message)
