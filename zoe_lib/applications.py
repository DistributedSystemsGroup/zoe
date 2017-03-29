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
import re

from zoe_lib.exceptions import InvalidApplicationDescription
import zoe_lib.version

log = logging.getLogger(__name__)


def app_validate(data):
    """
    Validates an application description, making sure all required fields are present and of the correct type.
    This validation is also performed on the Zoe Master side.
    If the description is not valid, an InvalidApplicationDescription exception is thrown.

    :param data: a dictionary containing an application description
    :return: None if the application description is correct
    """
    required_keys = ['name', 'will_end', 'priority', 'requires_binary', 'version']
    for k in required_keys:
        if k not in data:
            raise InvalidApplicationDescription(msg="Missing required key: %s" % k)

    try:
        ver = int(data["version"])
        if ver != zoe_lib.version.ZOE_APPLICATION_FORMAT_VERSION:
            raise InvalidApplicationDescription(msg="This version of Zoe supports only version {} for application descriptions".format(zoe_lib.version.ZOE_APPLICATION_FORMAT_VERSION))
    except ValueError:
        raise InvalidApplicationDescription(msg="version field should be an int")

    try:
        bool(data['will_end'])
    except ValueError:
        raise InvalidApplicationDescription(msg="will_end field must be a boolean")

    try:
        bool(data['requires_binary'])
    except ValueError:
        raise InvalidApplicationDescription(msg="requires_binary field must be a boolean")

    try:
        priority = int(data['priority'])
    except ValueError:
        raise InvalidApplicationDescription(msg="priority field must be an int")
    if priority < 0 or priority > 1024:
        raise InvalidApplicationDescription(msg="priority must be between 0 and 1024")

    if 'services' not in data:
        raise InvalidApplicationDescription(msg='the application should contain a list of services')

    _validate_all_services(data['services'])

def _validate_all_services(data):
    print(data)
    for service in data:
        print(service)
        _service_check(service)

    found_monitor = False
    for service in data:
        if service['monitor']:
            found_monitor = True
            break
    if not found_monitor:
        raise InvalidApplicationDescription(msg="at least one process should have monitor set to True")

def _service_check(data):
    """Check the service description schema."""
    required_keys = ['name', 'docker_image', 'monitor', 'ports', 'required_resources', 'total_count', 'essential_count', 'startup_order']
    for k in required_keys:
        if k not in data:
            raise InvalidApplicationDescription(msg="Missing required key: %s" % k)

    if not re.match(r'^[a-zA-Z0-9\-]+$', data['name']):
        raise InvalidApplicationDescription("Service name can contain only letters, numbers and dashes. '{}' is not valid.".format(data['name']))

    try:
        bool(data['monitor'])
    except ValueError:
        raise InvalidApplicationDescription(msg="monitor field should be a boolean")

    try:
        int(data['total_count'])
    except ValueError:
        raise InvalidApplicationDescription(msg="total_count field should be an int")

    try:
        int(data['essential_count'])
    except ValueError:
        raise InvalidApplicationDescription(msg="essential_count field should be an int")

    try:
        int(data['startup_order'])
    except ValueError:
        raise InvalidApplicationDescription(msg="start_order field should be an int")

    if not hasattr(data['ports'], '__iter__'):
        raise InvalidApplicationDescription(msg='ports should be a list')
    for service_port in data['ports']:
        _port_check(service_port)

    if not isinstance(data['required_resources'], dict):
        raise InvalidApplicationDescription(msg="required_resources should be a dictionary")
    if 'memory' not in data['required_resources']:
        data['required_resources']['memory'] = 0
    if 'cores' not in data['required_resources']:
        data['required_resources']['cores'] = 0
    try:
        int(data['required_resources']['memory'])
    except ValueError:
        raise InvalidApplicationDescription(msg="required_resources -> memory field should be an int")

    try:
        float(data['required_resources']['cores'])
    except ValueError:
        raise InvalidApplicationDescription(msg="required_resources -> cores field should be a float")

    if 'environment' in data:
        if not hasattr(data['environment'], '__iter__'):
            raise InvalidApplicationDescription(msg='environment should be an iterable')
        for e in data['environment']:
            if len(e) != 2:
                raise InvalidApplicationDescription(msg='environment variable should have a name and a value')
            if not isinstance(e[0], str):
                raise InvalidApplicationDescription(msg='environment variable names must be strings: {}'.format(e[0]))
            if not isinstance(e[1], str):
                raise InvalidApplicationDescription(msg='environment variable values must be strings: {}'.format(e[1]))

    if 'volumes' in data:
        if not hasattr(data['volumes'], '__iter__'):
            raise InvalidApplicationDescription(msg='volumes should be an iterable')
        for volume in data['volumes']:
            if len(volume) != 3:
                raise InvalidApplicationDescription(msg='volume description should have three components')
            if not isinstance(volume[2], bool):
                raise InvalidApplicationDescription(msg='readonly volume item (third) must be a boolean: {}'.format(volume[2]))

    if 'replicas' not in data:
        data['replicas'] = 1
    try:
        int(data['replicas'])
    except ValueError:
        raise InvalidApplicationDescription(msg="replicas field should be an int")


def _port_check(data):
    """Check the port description schema."""
    required_keys = ['name', 'protocol', 'port_number', 'is_main_endpoint']
    for k in required_keys:
        if k not in data:
            raise InvalidApplicationDescription(msg="Missing required key: %s" % k)

    try:
        int(data['port_number'])
    except ValueError:
        raise InvalidApplicationDescription(msg="port_number field should be an integer")

    try:
        bool(data['is_main_endpoint'])
    except ValueError:
        raise InvalidApplicationDescription(msg="is_main_endpoint field should be a boolean")
