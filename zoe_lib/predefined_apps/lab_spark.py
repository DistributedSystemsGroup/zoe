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


def spark_master_proc(mem_limit: int, image: str) -> dict:
    proc = {
        'name': "spark-master",
        'docker_image': image,
        'monitor': False,
        'required_resources': {"memory": mem_limit},
        'ports': [
            {
                'name': "Spark master web interface",
                'protocol': "http",
                'port_number': 8080,
                'path': "/",
                'is_main_endpoint': False
            }
        ],
        'environment': [
            ["SPARK_MASTER_IP", "spark-master-{execution_id}.zoe-usernet-{user_id}"]
        ]
    }
    return proc


def spark_worker_proc(count: int, mem_limit: int, cores: int, image: str) -> list:
    worker_ram = mem_limit - (1024 ** 3)
    ret = []
    for i in range(count):
        proc = {
            'name': "spark-worker-{}".format(i),
            'docker_image': image,
            'monitor': False,
            'required_resources': {"memory": mem_limit},
            'ports': [
                {
                    'name': "Spark worker web interface",
                    'protocol': "http",
                    'port_number': 8081,
                    'path': "/",
                    'is_main_endpoint': False
                }
            ],
            'environment': [
                ["SPARK_WORKER_CORES", str(cores)],
                ["SPARK_WORKER_RAM", str(worker_ram)],
                ["SPARK_MASTER_IP", "spark-master-{execution_id}.zoe-usernet-{user_id}"],
                ["SPARK_LOCAL_IP", "spark-worker-" + str(i) + "-{execution_id}.zoe-usernet-{user_id}"]
            ]
        }
        ret.append(proc)
    return ret


def spark_jupyter_notebook_proc(mem_limit: int, worker_mem_limit: int, image: str) -> dict:
    executor_ram = worker_mem_limit - (2 * 1024 ** 3)
    proc = {
        'name': "spark-jupyter",
        'docker_image': image,
        'monitor': True,
        'required_resources': {"memory": mem_limit},
        'ports': [
            {
                'name': "Spark application web interface",
                'protocol': "http",
                'port_number': 4040,
                'path': "/",
                'is_main_endpoint': False
            },
            {
                'name': "Jupyter Notebook interface",
                'protocol': "http",
                'port_number': 8888,
                'path': "/",
                'is_main_endpoint': True
            }
        ],
        'environment': [
            ["SPARK_MASTER", "spark://spark-master-{execution_id}.zoe-usernet-{user_id}:7077"],
            ["SPARK_EXECUTOR_RAM", str(executor_ram)]
        ]
    }
    return proc


def spark_jupyter_notebook_lab_app(name='spark-jupyter-lab',
                                   master_mem_limit=3 * (1024 ** 3),
                                   worker_count=3,
                                   worker_mem_limit=4 * (1024 ** 3),
                                   worker_cores=4,
                                   master_image='192.168.45.252:5000/zoerepo/spark-master',
                                   worker_image='192.168.45.252:5000/zoerepo/spark-worker',
                                   notebook_image='192.168.45.252:5000/zoerepo/spark-jupyter-notebook') -> dict:
    app = {
        'name': name,
        'version': 1,
        'will_end': False,
        'priority': 512,
        'requires_binary': False,
        'processes': [
            spark_master_proc(master_mem_limit, master_image),
            spark_jupyter_notebook_proc(master_mem_limit, worker_mem_limit, notebook_image)
        ] + spark_worker_proc(worker_count, worker_mem_limit, worker_cores, worker_image)
    }
    return app
