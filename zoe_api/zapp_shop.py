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

"""Zoe App shop module."""

import logging
import os
import json

import markdown

from zoe_lib.config import get_conf

log = logging.getLogger(__name__)

ZAPP_MANIFEST_VERSION = 1  # The manifest version this Zoe Shop can understand


class ZAppParameter:
    """A ZApp parameter that should be exposed to the user interface."""
    def __init__(self, param_manifest):
        self.kind = param_manifest['kind']
        self.name = param_manifest['name']
        self.readable_name = param_manifest['readable_name']
        self.description = param_manifest['description']
        self.default = param_manifest['default']
        if param_manifest['type'] == 'string':  # convert to HTML5 input types
            self.type = "text"
        elif param_manifest['type'] == 'int':
            self.type = "number"
        else:
            self.type = "text"


class ZApp:
    """A ZApp."""
    def __init__(self, zapp_id, manifest, manifest_index):
        self.id = zapp_id
        self.manifest_index = manifest_index
        zapp = manifest['zapps'][manifest_index]
        self.category = zapp['category']
        self.readable_name = zapp['name']
        self.readable_description_file = zapp['readable_descr']
        self.readable_description = self.read_description()
        self.json_file = zapp['description']
        self.zoe_description = self.parse_json_description()
        self.parameters = []
        self.parse_parameters(zapp)
        if 'guest_access' in zapp:
            self.guest_access = zapp['guest_access']
        else:
            self.guest_access = False
        if 'logo' in zapp:
            self.logo = zapp['logo']
        else:
            self.logo = 'logo.png'

    def parse_parameters(self, zapp_manifest):
        """Translates the parameters from the manifest into objects."""
        for param in zapp_manifest['parameters']:
            self.parameters.append(ZAppParameter(param))

    def read_description(self):
        """Reads and renders the README.md file."""
        mdown = open(os.path.join(get_conf().zapp_shop_path, self.id, self.readable_description_file), 'r', encoding='utf-8').read()
        return markdown.markdown(mdown, extensions=['markdown.extensions.extra', 'markdown.extensions.codehilite'])

    def parse_json_description(self):
        """Reads the classic json description."""
        return json.load(open(os.path.join(get_conf().zapp_shop_path, self.id, self.json_file), 'r'))


def zshop_list_apps(role):
    """List the ZApp repos."""
    dirs = [d for d in os.listdir(get_conf().zapp_shop_path) if os.path.isdir(os.path.join(get_conf().zapp_shop_path, d)) and os.path.exists(os.path.join(get_conf().zapp_shop_path, d, "manifest.json"))]

    zapps = []
    for adir in dirs:
        zapps += zshop_read_manifest(adir)

    zapp_cat = {}
    for zapp in zapps:
        if role == 'guest' and not zapp.guest_access:
            continue
        if zapp.category in zapp_cat:
            zapp_cat[zapp.category].append(zapp)
        else:
            zapp_cat[zapp.category] = [zapp]
    return zapp_cat


def zshop_read_manifest(zapp_id):
    """Reads and decodes the manifest file."""
    manifest_path = os.path.join(get_conf().zapp_shop_path, zapp_id, "manifest.json")
    manifest = json.load(open(manifest_path))
    if manifest['version'] != ZAPP_MANIFEST_VERSION:
        log.warning("Cannot load ZApp {}, this Zoe understands manifests version {} only".format(zapp_id, ZAPP_MANIFEST_VERSION))
        return []
    zapps = []
    for idx in range(len(manifest['zapps'])):
        zapps.append(ZApp(zapp_id, manifest, idx))
    return zapps


def get_logo(zapp: ZApp):
    """Return the ZApp PNG logo image file contents."""
    logo_path = os.path.join(get_conf().zapp_shop_path, zapp.id, zapp.logo)
    return open(logo_path, "rb").read()
