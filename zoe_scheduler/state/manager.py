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

import logging
import json

from zoe_lib.exceptions import ZoeException
from zoe_scheduler.config import get_conf
from zoe_scheduler.state.user import User
from zoe_scheduler.state.application import Application
from zoe_scheduler.state.execution import Execution
from zoe_scheduler.state.container import Container
from zoe_scheduler.state.blobs import BaseBlobs

log = logging.getLogger(__name__)


class StateManager:
    """
    :type _next_id: int
    :type _state_epoch: int
    :type blobs: BaseBlobs
    """
    def __init__(self, blob_class):
        self.applications = {}
        self.users = {}
        self.executions = {}
        self.containers = {}

        self._next_id = 1  # 0 is always the zoeadmin user

        self._state_epoch = 1

        self.blobs = blob_class()
        self.blobs.init()

    def init(self, checkpoint=None, reset_checkpoints=False):
        if reset_checkpoints:
            ckps = self.blobs.list_blobs('checkpoint')
            log.warning('Deleting all state checkpoints, Zoe state will be lost')
            for ckp in ckps:
                self.blobs.delete_blob('checkpoint', ckp)

        if checkpoint is None:
            highest_epoch = self._find_latest_checkpoint()
            if highest_epoch is not None:
                checkpoint = highest_epoch

        if checkpoint is None:
            log.info('Starting with initial state, no checkpoints found')
        else:
            try:
                self.load_checkpoint(checkpoint)
            except:
                log.exception('Corrupted state checkpoint ({}), starting with empty state'.format(checkpoint))

        if self.get_one('user', id=0) is None:
            log.warn('No Zoe admin user found, creating a new one. This is normal the first time Zoe is run.')
            admin = User(self)
            admin.id = 0
            admin.role = "admin"
            admin.name = 'zoeadmin'
            admin.set_password(get_conf().zoeadmin_password)
            self.new('user', admin)
        else:
            admin = self.get_one('user', id=0)
            if not admin.verify_password(get_conf().zoeadmin_password):  # master password changed in the config file
                log.warning('zoeadmin password has changed')
                admin.set_password(get_conf().zoeadmin_password)

    def _find_latest_checkpoint(self):
        ckps = self.blobs.list_blobs('checkpoint')
        highest_ckp = None
        highest_epoch = 0
        for ckp_file in ckps:
            blob = self.blobs.load_blob('checkpoint', str(ckp_file))
            ckp = json.loads(blob.decode('utf-8'))
            if ckp['state_manager']['state_epoch'] > highest_epoch:
                highest_ckp = ckp_file
                highest_epoch = ckp['state_manager']['state_epoch']
        return highest_ckp

    def generate_checkpoint(self):
        checkpointed_state = {
            'users': [u.checkpoint() for u in self.users.values()],
            'applications': [a.checkpoint() for a in self.applications.values()],
            'executions': [e.checkpoint() for e in self.executions.values()],
            'containers': [c.checkpoint() for c in self.containers.values()],
            'state_manager': {
                'next_id': self._next_id,
                'state_epoch': self._state_epoch
            }
        }
        ckp_name = str(self._state_epoch % 10)
        ckp = json.dumps(checkpointed_state)
        blob = ckp.encode('utf-8')
        self.blobs.store_blob('checkpoint', ckp_name, blob)

    def load_checkpoint(self, epoch):
        blob = self.blobs.load_blob('checkpoint', str(epoch))
        ckp = blob.decode('utf-8')
        state = json.loads(ckp)
        self._next_id = state['state_manager']['next_id']
        self._state_epoch = state['state_manager']['state_epoch']
        log.info('Loading checkpoint with state epoch {}'.format(self._state_epoch))
        for u in state['users']:
            us = User(self)
            us.load_checkpoint(u)
            self.users[us.id] = us
        for a in state['applications']:
            ap = Application(self)
            ap.load_checkpoint(a)
            self.applications[ap.id] = ap
        for e in state['executions']:
            ex = Execution(self)
            ex.load_checkpoint(e)
            self.executions[ex.id] = ex
        for c in state['containers']:
            co = Container(self)
            co.load_checkpoint(c)
            self.containers[co.id] = co

    def state_updated(self):
        self._state_epoch += 1
        log.debug('New state epoch, generating checkpoint')
        self.generate_checkpoint()

    def gen_id(self) -> int:
        log.debug('Generating ID {}'.format(self._next_id))
        self._next_id += 1
        return self._next_id - 1

    def _matches(self, obj, filter):
        field = filter[0]
        value = filter[1]
        if field == 'owner':
            return obj.owner == value
        if hasattr(obj, field) and getattr(obj, field) == value:
            return True
        else:
            return False

    def get_one(self, what, **kwargs):
        res = self.get(what, **kwargs)
        if len(res) > 0:
            return res[0]
        else:
            return None

    def get(self, what, **kwargs):
        """
        Query the state
        :param what: one of user, application, execution, container
        :return: all objects of type 'what' with fields matching all filters (AND)
        """

        try:
            collection = getattr(self, what + 's')
        except AttributeError:
            raise ZoeException('Unknown query: {}'.format(what))

        result = []
        for obj in collection.values():
            res = True
            for k, v in kwargs.items():
                res = res and self._matches(obj, (k, v))
            if res:
                result.append(obj)

        return result

    def delete(self, what, obj_id: int):
        try:
            collection = getattr(self, what + 's')
        except AttributeError:
            log.error('Trying to delete an unknown object: {}'.format(what))
            return

        if what == 'execution':
            self.blobs.delete_blob('logs', str(obj_id))

        if what == 'container':
            c = self.containers[obj_id]
            c.execution.containers.remove(c)

        if obj_id in collection:
            del collection[obj_id]

        return

    def new(self, what, obj) -> int:
        try:
            collection = getattr(self, what + 's')
        except AttributeError:
            log.error('Trying to create an object in an unknown collection: {}'.format(what))
            return

        assert obj.id is not None

        collection[obj.id] = obj

        return

    def user_has_active_executions(self, user_id: int) -> bool:
        user = self.get_one('user', id=user_id)
        if user is None:
            return False
        for app in user.applications:
            ret = self.app_has_active_executions(app.id)
            if ret:
                return True
        return False

    def app_has_active_executions(self, app_id: int) -> bool:
        app = self.get_one('application', id=app_id)
        if app is None:
            return False
        for e in app.executions:
                if e.status == "running" or e.status == "scheduled":
                    return True
        return False
