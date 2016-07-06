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

"""RESTful Flask API definition."""

import sys
import pkgutil

from flask import Blueprint
from flask_restful import Api

from zoe_api.rest_api.execution import ExecutionAPI, ExecutionCollectionAPI, ExecutionDeleteAPI
from zoe_api.rest_api.info import InfoAPI
from zoe_api.rest_api.service import ServiceAPI

from zoe_lib.version import ZOE_API_VERSION

API_PATH = '/api/' + ZOE_API_VERSION


def api_init(api_endpoint) -> Blueprint:
    """Initialize the API"""
    api_bp = Blueprint('api', __name__)
    api = Api(api_bp, catch_all_404s=True)

    api.add_resource(InfoAPI, API_PATH + '/info', resource_class_kwargs={'api_endpoint': api_endpoint})
    api.add_resource(ExecutionAPI, API_PATH + '/execution/<int:execution_id>', resource_class_kwargs={'api_endpoint': api_endpoint})
    api.add_resource(ExecutionDeleteAPI, API_PATH + '/execution/delete/<int:execution_id>', resource_class_kwargs={'api_endpoint': api_endpoint})
    api.add_resource(ExecutionCollectionAPI, API_PATH + '/execution', resource_class_kwargs={'api_endpoint': api_endpoint})
    api.add_resource(ServiceAPI, API_PATH + '/service/<int:service_id>', resource_class_kwargs={'api_endpoint': api_endpoint})

    return api_bp

# Work around a Python 3.4.0 bug that affects Flask
if sys.version_info == (3, 4, 0, 'final', 0):
    ORIG_LOADER = pkgutil.get_loader

    def get_loader(name):
        """Wrap the original loader to catch a buggy exception."""
        try:
            return ORIG_LOADER(name)
        except AttributeError:
            pass

    pkgutil.get_loader = get_loader
