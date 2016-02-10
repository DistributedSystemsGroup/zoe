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


def hadoop_namenode_proc(image: str) -> dict:
    proc = {
        'name': "hdfs-namenode",
        'docker_image': image,
        'monitor': True,
        'required_resources': {"memory": 2 * 1024 * 1024 * 1024},  # 2 GB
        'ports': [
            {
                'name': "NameNode web interface",
                'protocol': "http",
                'port_number': 50070,
                'path': "/",
                'is_main_endpoint': True
            }
        ],
        'environment': [
            ["NAMENODE_HOST", "hdfs-namenode-{execution_id}"]
        ]
    }
    return proc


def hadoop_datanode_proc(count: int, image: str) -> list:
    ret = []
    for i in range(count):
        proc = {
            'name': "hdfs-datanode-{}".format(i),
            'docker_image': image,
            'monitor': False,
            'required_resources': {"memory": 1 * 1024 * 1024 * 1024},  # 1 GB
            'ports': [],
            'environment': [
                ["NAMENODE_HOST", "hdfs-namenode-{execution_id}"]
            ]
        }
        ret.append(proc)
    return ret


def hdfs_app(name='hdfs',
             namenode_image='192.168.45.252:5000/zoerepo/hadoop-namenode',
             datanode_count=3,
             datanode_image='192.168.45.252:5000/zoerepo/hadoop-datanode') -> dict:
    app = {
        'name': name,
        'version': 1,
        'will_end': False,
        'priority': 512,
        'requires_binary': False,
        'processes': [
            hadoop_namenode_proc(namenode_image),
        ] + hadoop_datanode_proc(datanode_count, datanode_image)
    }
    return app
