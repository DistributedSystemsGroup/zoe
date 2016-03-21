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

import zoe_lib.predefined_frameworks.jupyter_spark as jupyter_spark_framework
import zoe_lib.predefined_frameworks.spark as spark_framework


def spark_jupyter_notebook_app(name='spark-jupyter',
                               notebook_mem_limit=4 * (1024 ** 3),
                               master_mem_limit=512 * (1024 ** 2),
                               worker_count=2,
                               worker_mem_limit=12 * (1024 ** 3),
                               worker_cores=6,
                               master_image='192.168.45.252:5000/zoerepo/spark-master',
                               worker_image='192.168.45.252:5000/zoerepo/spark-worker',
                               notebook_image='192.168.45.252:5000/zoerepo/spark-jupyter-notebook'):
    """
    :type name: str
    :type notebook_mem_limit: int
    :type master_mem_limit: int
    :type worker_count: int
    :type worker_mem_limit: int
    :type worker_cores: int
    :type master_image: str
    :type worker_image: str
    :type notebook_image: str
    :rtype: dict
    """
    sp_master = spark_framework.spark_master_service(master_mem_limit, master_image)
    sp_workers = spark_framework.spark_worker_service(worker_count, worker_mem_limit, worker_cores, worker_image)

    app = {
        'name': name,
        'version': 1,
        'will_end': False,
        'priority': 512,
        'requires_binary': False,
        'services': [
            sp_master,
            jupyter_spark_framework.spark_jupyter_notebook_service(notebook_mem_limit, worker_mem_limit, notebook_image)
        ] + sp_workers
    }
    return app
