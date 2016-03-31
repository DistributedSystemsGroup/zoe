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

from zoe_master.state.user import User


def test_manager(state_manager):
    user = User(state_manager)
    user_id = state_manager.gen_id()
    user.id = user_id
    state_manager.new('user', user)
    assert state_manager.users[user_id] == user
    guser = state_manager.get_one('user', id=user_id)
    assert guser == user
    state_manager.delete('user', user_id)
