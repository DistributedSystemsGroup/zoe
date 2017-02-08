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

"""The ZApp packaging definition."""

import json
import os

from jsonschema import validate as json_schema_validate, ValidationError

from zoe_api.exceptions import ZoeException
from zoe_lib.config import get_conf

PACKAGE_VERSION = 1

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
METADATA_SCHEMA_PATH = os.path.realpath(os.path.join(__location__, "..", "..", "schemas", "zapp_metadata_schema.json"))


class ZAppPackage:
    """A ZApp package."""
    METADATA_FILE = 'metadata.json'
    TEMPLATE_FILE = 'services.json'
    DOCS_FILE = 'README.md'

    def __init__(self, load_path):
        self.load_path = load_path
        self.id = ''
        # Metadata
        self.name = ''
        self.version = ''
        self.package_version = 0
        self.maintainer = ''
        self.license = ''

        self.sanity_check()

        self._load_metadata()

    def sanity_check(self):
        """Check that a ZApp package is in the right format."""
        if not os.access(os.path.join(self.load_path, self.METADATA_FILE), os.R_OK):
            raise ZoeException('No metadata file in ZApp package at {}'.format(self.load_path))

        if not os.access(os.path.join(self.load_path, self.DOCS_FILE), os.R_OK):
            raise ZoeException('No readme file in ZApp package at {}'.format(self.load_path))

        if not os.access(os.path.join(self.load_path, self.TEMPLATE_FILE), os.R_OK):
            raise ZoeException('No template file in ZApp package at {}'.format(self.load_path))

    def _load_metadata(self):
        fpath = os.path.join(self.load_path, self.METADATA_FILE)
        schema = json.load(open(METADATA_SCHEMA_PATH, 'r'))
        metadata = json.load(open(fpath, 'r'))
        json_schema_validate(metadata, schema)

        # Code for handling previous package versions goes here
        self.package_version = metadata['package_version']

        self.name = metadata['name']
        self.version = metadata['version']
        self.maintainer = metadata['maintainer']
        self.license = metadata['license']
        self.id = self.name + ':' + self.version

    def _load_template(self):
        fpath = os.path.join(self.load_path, self.TEMPLATE_FILE)
        return json.load(open(fpath, 'r'))

    def generate_app_description(self):
        """Generate a Zoe application description by instantiating the template."""
        template = self._load_template()

        app_descr = {
            'name': self.name,
            'services': [],
            'version': 3,
        }

        for service in template['services']:
            service['image'] = get_conf().registry + '/' + get_conf().registry_repository + '/' + service['image'] + ":" + self.version

            app_descr['services'].append(service)

        return app_descr
