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
"""
This package contains the Zoe library, with modules used by more than one of the Zoe components. This library can also be used to write new clients for Zoe.
"""
from functools import wraps
import logging
import time

import requests
import requests.exceptions

from zoe_lib.version import ZOE_API_VERSION
from zoe_lib.exceptions import ZoeAPIException

log = logging.getLogger(__name__)


def retry(exception_to_check, tries=4, delay=3, backoff=2):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param exception_to_check: the exception to check. may be a tuple of
        exceptions to check
    :type exception_to_check: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    """
    def deco_retry(func):
        """Decorator to wrap calls that need to be retried."""
        @wraps(func)
        def f_retry(*args, **kwargs):
            """The actual decorator."""
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except exception_to_check as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    log.warning(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


class ZoeAPIBase:
    """Base class for the Zoe Client API."""
    def __init__(self, url, token):
        self.url = url
        self.token = token

    @retry(ZoeAPIException)
    def _rest_get_stream(self, path):
        """
        :type path: str
        :rtype: Tuple[requests.Response, int]
        """
        url = self.url + '/api/' + ZOE_API_VERSION + path
        try:
            req = requests.get(url, stream=True, headers={'Cookie': self.token})
        except requests.exceptions.Timeout:
            raise ZoeAPIException('HTTP connection timeout')
        except requests.exceptions.HTTPError:
            raise ZoeAPIException('Invalid HTTP response')
        except requests.exceptions.ConnectionError as e:
            raise ZoeAPIException('Connection error: {}'.format(e))

        return req, req.status_code

    @retry(ZoeAPIException)
    def _rest_get(self, path, payload=None):
        """
        :type path: str
        :type payload: dict
        :rtype: (dict, int)
        """
        url = self.url + '/api/' + ZOE_API_VERSION + path
        try:
            req = requests.get(url, params=payload, headers={'Cookie': self.token})
        except requests.exceptions.Timeout:
            raise ZoeAPIException('HTTP connection timeout')
        except requests.exceptions.HTTPError:
            raise ZoeAPIException('Invalid HTTP response')
        except requests.exceptions.ConnectionError as e:
            raise ZoeAPIException('Connection error: {}'.format(e))

        if not req.ok:
            data = req.reason
        else:
            data = req.json()
        return data, req.status_code

    @retry(ZoeAPIException)
    def _rest_post(self, path, payload):
        """
        :type path: str
        :rtype: (dict, int)
        """
        url = self.url + '/api/' + ZOE_API_VERSION + path
        try:
            req = requests.post(url, json=payload, headers={'Cookie': self.token})
        except requests.exceptions.Timeout:
            raise ZoeAPIException('HTTP connection timeout')
        except requests.exceptions.HTTPError:
            raise ZoeAPIException('Invalid HTTP response')
        except requests.exceptions.ConnectionError as e:
            raise ZoeAPIException('Connection error: {}'.format(e))

        if not req.ok:
            data = req.reason
        else:
            try:
                data = req.json()
            except ValueError:
                data = None
        return data, req.status_code

    @retry(ZoeAPIException)
    def _rest_delete(self, path):
        """
        :type path: str
        :rtype: (dict, int)
        """
        url = self.url + '/api/' + ZOE_API_VERSION + path
        try:
            req = requests.delete(url, headers={'Cookie': self.token})
        except requests.exceptions.Timeout:
            raise ZoeAPIException('HTTP connection timeout')
        except requests.exceptions.HTTPError:
            raise ZoeAPIException('Invalid HTTP response')
        except requests.exceptions.ConnectionError as e:
            raise ZoeAPIException('Connection error: {}'.format(e))

        if not req.ok:
            data = req.reason
        else:
            data = None
        return data, req.status_code
