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

from zoe_lib.exceptions import ZoeRestAPIException


def authentication_error():
    raise ZoeRestAPIException('Cannot authenticate your request, provide proper credentials', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


def authenticate(request, state):
    auth = request.authorization
    if not auth:
        authentication_error()
    user = state.get_one('user', name=auth.username)
    if user is None:
        authentication_error()
    if not user.verify_password(auth.password):
        authentication_error()
    else:
        return user
