#!/usr/bin/python3

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

"""
Manage ZApp packages.
"""

import logging

from zoe_lib.zapps.zapp_storage import ZAppStorage
from zoe_lib.zapps.zapp_package import ZAppPackage
import zoe_lib.config as config


def list_zapps():
    """List all ZApps available in the local store."""
    zapp_store = ZAppStorage()
    zapps = zapp_store.list()
    for zapp in zapps:  # type: ZAppPackage
        print('{} {} {} (by {})'.format(zapp.id, zapp.name, zapp.version, zapp.maintainer))


def load_zapp(id):
    """Loads a specific ZApp given its ID."""
    zapp_store = ZAppStorage()
    zapp = zapp_store.load(id)
    if zapp is None:
        print('Cannot find the {} ZApp'.format(id))
        return
    tmp = zapp.generate_app_description()
    import pprint; pprint.pprint(tmp)


def main():
    """Main entrypoint."""
    config.load_configuration()
    args = config.get_conf()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)

    load_zapp('sleeper:1.0')

if __name__ == '__main__':
    main()
