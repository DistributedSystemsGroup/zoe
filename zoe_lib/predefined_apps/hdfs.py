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

import zoe_lib.predefined_frameworks.hadoop as hadoop_framework


def hdfs_app(name='hdfs',
             namenode_image='192.168.45.252:5000/zoerepo/hadoop-namenode',
             datanode_count=3,
             datanode_image='192.168.45.252:5000/zoerepo/hadoop-datanode'):
    """
    :type name: str
    :type namenode_image: str
    :type datanode_count: int
    :type datanode_image: str
    :rtype: dict
    """
    app = {
        'name': name,
        'version': 1,
        'will_end': False,
        'priority': 512,
        'requires_binary': False,
        'services': [
            hadoop_framework.hadoop_namenode_service(namenode_image),
        ] + hadoop_framework.hadoop_datanode_service(datanode_count, datanode_image)
    }
    return app


def hdfs_client_app(name='hdfs-client',
                    image='192.168.45.252:5000/zoerepo/hadoop-client',
                    namenode='hdfs-namenode.hdfs',
                    user='root',
                    command='hdfs dfs -ls /'):
    """
    :type name: str
    :type image: str
    :type user: str
    :type namenode: str
    :type command: str
    :rtype: dict
    """
    app = {
        'name': name,
        'version': 1,
        'will_end': True,
        'priority': 512,
        'requires_binary': False,
        'services': [
            hadoop_framework.hadoop_client_service(image, namenode, user, command)
        ]
    }
    return app
