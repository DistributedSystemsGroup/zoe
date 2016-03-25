# Copyright (c) 2016, Daniele Venzano
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

import zoe_lib.predefined_frameworks.spark as spark_framework


def spark_submit_app(name='spark-submit',
                     master_mem_limit=4 * 1024 * 1024 * 1024,
                     worker_count=3,
                     worker_mem_limit=8 * 1024 * 1024 * 1024,
                     worker_cores=4,
                     master_image='192.168.45.252:5000/zoerepo/spark-master',
                     worker_image='192.168.45.252:5000/zoerepo/spark-worker',
                     submit_image='192.168.45.252:5000/zoerepo/spark-submit',
                     commandline='wordcount.py hdfs://192.168.45.157/datasets/gutenberg_big_2x.txt hdfs://192.168.45.157/tmp/cntwdc1'):
    """
    :type name: str
    :type master_mem_limit: int
    :type worker_count: int
    :type worker_mem_limit: int
    :type worker_cores: int
    :type master_image: str
    :type worker_image: str
    :type submit_image: str
    :type commandline: str
    :rtype: dict
    """
    app = {
        'name': name,
        'version': 1,
        'will_end': False,
        'priority': 512,
        'requires_binary': True,
        'services': [
            spark_framework.spark_master_service(master_mem_limit, master_image),
            spark_framework.spark_submit_service(master_mem_limit, worker_mem_limit, submit_image, commandline)
        ] + spark_framework.spark_worker_service(worker_count, worker_mem_limit, worker_cores, worker_image)
    }
    return app
