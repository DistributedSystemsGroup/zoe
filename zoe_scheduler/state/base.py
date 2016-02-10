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

from zoe_lib.exceptions import ZoeException

log = logging.getLogger(__name__)


class BaseState:
    api_in_attrs = []
    api_out_attrs = []
    private_attrs = []

    def __init__(self, state):
        self.id = None
        self.api_out_attrs.append('id')

        self.state_manger = state

    def checkpoint(self):
        ck_dict = self.to_dict(checkpoint=True)
        ck_dict['class'] = type(self).__name__
        return ck_dict

    def load_checkpoint(self, ck_dict):
        if ck_dict['class'] != type(self).__name__:
            log.error('Type mismatch during de-serialization of class "%s" trying to decode a "%s"' % (type(self).__name__, ck_dict['class']))
            raise ZoeException('Type mismatch during de-serialization')

        self.from_dict(ck_dict, checkpoint=True)

    def to_dict(self, checkpoint):
        attrs = set(self.api_out_attrs)
        if checkpoint:
            attrs.update(self.api_in_attrs)
            attrs.update(self.private_attrs)

        d = {}
        for a in attrs:
            d[a] = getattr(self, a)

        return d

    def from_dict(self, d, checkpoint):
        attrs = set(self.api_in_attrs)
        if checkpoint:
            attrs = set(self.api_out_attrs)
            attrs.update(self.private_attrs)
        for a in attrs:
            try:
                setattr(self, a, d[a])
            except KeyError:
                raise ZoeException('Missing required attribute {}'.format(a))

    @property
    def owner(self):
        raise NotImplementedError

    def __eq__(self, other):
        return self.id == other.id
