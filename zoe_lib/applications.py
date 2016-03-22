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

from zoe_lib.exceptions import InvalidApplicationDescription, ZoeAPIException
from zoe_lib.predefined_apps import PREDEFINED_APPS

log = logging.getLogger(__name__)


def predefined_app_list():
    """
    Returns a list of predefined application available

    :return: a list of application names
    """
    name_list = []
    for gen_app in PREDEFINED_APPS:
        app = gen_app()
        name_list.append(app['name'])
    return name_list


def predefined_app_generate(name):
    """
    Returns the predefined application corresponding to the name given as argument

    :param name: the name of the application to generate
    :return: an application dictionary
    """
    for gen_app in PREDEFINED_APPS:
        app = gen_app()
        if app['name'] == name:
            return app
    raise ZoeAPIException('No such predefined application')


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
        int(data["version"])
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

    for p in data['services']:
        _service_check(p)

    found_monitor = False
    for p in data['services']:
        if p['monitor']:
            found_monitor = True
            break
    if not found_monitor:
        raise InvalidApplicationDescription(msg="at least one process should have monitor set to True")


def _service_check(data):
    required_keys = ['name', 'docker_image', 'monitor', 'ports', 'required_resources']
    for k in required_keys:
        if k not in data:
            raise InvalidApplicationDescription(msg="Missing required key: %s" % k)

    try:
        bool(data['monitor'])
    except ValueError:
        raise InvalidApplicationDescription(msg="monitor field should be a boolean")

    if not hasattr(data['ports'], '__iter__'):
        raise InvalidApplicationDescription(msg='ports should be a list')
    for pp in data['ports']:
        _port_check(pp)

    if not isinstance(data['required_resources'], dict):
        raise InvalidApplicationDescription(msg="required_resources should be a dictionary")
    if 'memory' not in data['required_resources']:
        raise InvalidApplicationDescription(msg="Missing required key: required_resources -> memory")
    try:
        int(data['required_resources']['memory'])
    except ValueError:
        raise InvalidApplicationDescription(msg="required_resources -> memory field should be an int")

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
        for v in data['volumes']:
            if len(v) != 3:
                raise InvalidApplicationDescription(msg='volume description should have three components')
            if not isinstance(v[2], bool):
                raise InvalidApplicationDescription(msg='readonly volume item (third) must be a boolean: {}'.format(v[2]))

    if 'networks' in data:
        if not hasattr(data['networks'], '__iter__'):
            raise InvalidApplicationDescription(msg='networks should be an iterable')


def _port_check(data):
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
