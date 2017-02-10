# Copyright (c) 2017, Daniele Venzano
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

"""The ZApp storage manager. It adds, lists, loads and deletes ZApps from the internal store."""

import os

from zoe_lib.config import get_conf
from zoe_lib.exceptions import ZoeLibException
from zoe_lib.zapps.zapp_package import ZAppPackage

ZAPP_STORAGE_PATH = 'zapps'


class ZAppStorage:
    """The ZApp storage manager. It adds, lists, loads and deletes ZApps from the internal store."""
    def __init__(self):
        self.path = os.path.join(get_conf().zapp_storage, ZAPP_STORAGE_PATH)
        try:
            os.makedirs(self.path, exist_ok=True)
        except OSError:
            raise ZoeLibException(message='Cannot create directory {}'.format(self.path))

    def list(self):
        """Loads all ZApps from the storage directory and returns a list of ZAppPackage objects."""
        all_zapps = []
        for zapp_dir in os.listdir(self.path):
            zapp = ZAppPackage(os.path.join(self.path, zapp_dir))
            all_zapps.append(zapp)

        return all_zapps

    def load(self, zapp_id):
        """Loads a specific ZApp given its ID."""
        zapps = self.list()
        for zapp in zapps:
            if zapp.id == zapp_id:
                return zapp
        return None
