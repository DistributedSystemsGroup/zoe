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


def sleeper_service(sleep_duration):
    """
    :type sleep_duration: int
    :rtype: dict
    """
    service = {
        'name': "sleeper",
        'docker_image': 'alpine',
        'monitor': True,
        'required_resources': {"memory": 1 * 1024 * 1024 * 1024},  # 1 GB
        'ports': [],
        'environment': [],
        'command': 'sleep ' + str(sleep_duration)
    }
    return service


def sleeper_app(name='sleeper', sleep_duration=5):
    """
    :param name:
    :param sleep_duration:
    :rtype: dict
    """
    app = {
        'name': name,
        'version': 1,
        'will_end': True,
        'priority': 512,
        'requires_binary': False,
        'services': [
            sleeper_service(sleep_duration)
        ]
    }
    return app
