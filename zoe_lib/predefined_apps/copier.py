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


def copier_proc(source, dest) -> dict:
    proc = {
        'name': "copier",
        'docker_image': 'alpine',
        'monitor': True,
        'required_resources': {"memory": 512 * 1024 * 1024},  # 512MB
        'ports': [],
        'environment': [],
        'volumes': [],
        'command': ''
    }
    if source['type'] == 'volume':
        proc['volumes'].append([source['host_path'], '/mnt/source', True])
    if dest['type'] == 'volume':
        proc['volumes'].append([dest['host_path'], '/mnt/dest', False])

    if source['type'] == 'volume' and dest['type'] == 'volume':
        proc['command'] = 'cp -a /mnt/source/' + source['name'] + ' /mnt/dest' + dest['name']

    return proc

empty = {
    'type': 'volume',
    'host_path': 'CHANGEME',  # the path containing what to copy
    'name': 'CHANGEME'  # the file or directory to copy from or to host_path
}


def copier_app(source=empty, dest=empty) -> dict:
    app = {
        'name': 'copier',
        'version': 1,
        'will_end': True,
        'priority': 512,
        'requires_binary': False,
        'processes': [
            copier_proc(source, dest)
        ]
    }
    return app
