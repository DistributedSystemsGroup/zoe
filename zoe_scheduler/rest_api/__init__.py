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

import sys
from flask import Flask
from flask_restful import Api

from zoe_scheduler.rest_api.user import UserAPI, UserCollectionAPI
from zoe_scheduler.rest_api.execution import ExecutionAPI, ExecutionCollectionAPI
from zoe_scheduler.rest_api.container import ContainerAPI
from zoe_scheduler.rest_api.query import QueryAPI
from zoe_scheduler.rest_api.info import InfoAPI
from zoe_lib.version import ZOE_API_VERSION

API_PATH = '/api/' + ZOE_API_VERSION


def init(state, platform) -> Flask:
    app = Flask("Zoe REST API")
    api = Api(app, catch_all_404s=True)

    args = {
        'state': state,
        'platform': platform
    }

    api.add_resource(InfoAPI, API_PATH + '/info', resource_class_kwargs=args)
    api.add_resource(UserAPI, API_PATH + '/user/<int:user_id>', resource_class_kwargs=args)
    api.add_resource(UserCollectionAPI, API_PATH + '/user', resource_class_kwargs=args)
    api.add_resource(ExecutionAPI, API_PATH + '/execution/<int:execution_id>', resource_class_kwargs=args)
    api.add_resource(ExecutionCollectionAPI, API_PATH + '/execution', resource_class_kwargs=args)
    api.add_resource(ContainerAPI, API_PATH + '/container/<int:container_id>', resource_class_kwargs=args)
    api.add_resource(QueryAPI, API_PATH + '/query', resource_class_kwargs=args)

    return app

# Work around a Python 3.4.0 bug that affects Flask
if sys.version_info == (3, 4, 0, 'final', 0):
    import pkgutil
    orig_get_loader = pkgutil.get_loader


    def get_loader(name):
        try:
            return orig_get_loader(name)
        except AttributeError:
            pass

    pkgutil.get_loader = get_loader
