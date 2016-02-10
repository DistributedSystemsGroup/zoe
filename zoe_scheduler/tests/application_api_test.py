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

from zoe_scheduler.state.application import Application
from zoe_scheduler.state.user import User


def test_from_dict(application_dict, state_manager):
    dummy_user = User(state_manager)
    dummy_user.id = state_manager.gen_id()
    state_manager.new('user', dummy_user)
    application_dict['user_id'] = dummy_user.id
    dummy_app = Application(state_manager)
    dummy_app.from_dict(application_dict, checkpoint=False)
