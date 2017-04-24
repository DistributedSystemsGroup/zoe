# Copyright (c) 2015, Daniele Venzano
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
This module contains code to validate application descriptions.
"""

import logging
import json

import jsonschema

from zoe_lib.exceptions import InvalidApplicationDescription, ZoeLibException
import zoe_lib.version

log = logging.getLogger(__name__)


def app_validate(data):
    """
    Validates an application description, making sure all required fields are present and of the correct type.
    If the description is not valid, an InvalidApplicationDescription exception is thrown.
    Uses a JSON schema definition.

    :param data: an open file descriptor containing JSON data
    :return: None if the application description is correct
    """

    schema = json.load(open('schemas/app_description_schema.json', 'r'))
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        raise InvalidApplicationDescription(str(e))
    except jsonschema.SchemaError:
        log.exception('BUG: invalid schema for application descriptions')
        raise ZoeLibException('BUG: invalid schema for application descriptions')

    # Start non-schema, semantic checks
    if data['version'] != zoe_lib.version.ZOE_APPLICATION_FORMAT_VERSION:
        raise InvalidApplicationDescription('Application description version mismatch (expected: {}, found: {}'.format(zoe_lib.version.ZOE_APPLICATION_FORMAT_VERSION, data['version']))

    found_monitor = False
    for service in data['services']:
        if service['monitor']:
            found_monitor = True
            break
        if service['resources']['memory']['min'] > service['resources']['memory']['max']:
            raise InvalidApplicationDescription(msg='service {} has mismatching min and max memory limits'.format(service['name']))
        if service['resources']['cores']['min'] > service['resources']['cores']['max']:
            raise InvalidApplicationDescription(msg='service {} has mismatching min and max memory limits'.format(service['name']))

    if not found_monitor:
        raise InvalidApplicationDescription(msg="at least one process should have the monitor property set to true")
