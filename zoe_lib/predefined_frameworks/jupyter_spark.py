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


def spark_jupyter_notebook_service(mem_limit, worker_mem_limit, image):
    """
    :type mem_limit: int
    :type worker_mem_limit: int
    :type image: str
    :rtype: dict
    """
    executor_ram = worker_mem_limit - (1024 ** 3) - (512 * 1025 ** 2)
    driver_ram = (2 * 1024 ** 3)
    service = {
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
            ["SPARK_MASTER", "spark://spark-master-{execution_name}-{user_name}-{deployment_name}-zoe.{user_name}-{deployment_name}-zoe:7077"],
            ["SPARK_EXECUTOR_RAM", str(executor_ram)],
            ["SPARK_DRIVER_RAM", str(driver_ram)],
            ["NB_USER", "{user_name}"]
        ],
        'networks': []
    }
    return service

