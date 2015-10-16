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

from common.application_description import ZoeProcessEndpoint, ZoeApplicationProcess, ZoeApplication


def spark_master_proc(mem_limit: int, image: str) -> ZoeApplicationProcess:
    proc = ZoeApplicationProcess()
    proc.name = "spark-master"
    proc.docker_image = image
    proc.monitor = False
    proc.required_resources["memory"] = mem_limit
    port = ZoeProcessEndpoint()
    port.name = "Spark master web interface"
    port.protocol = "http"
    port.port_number = 8080
    port.path = "/"
    port.is_main_endpoint = False
    proc.ports.append(port)
    proc.environment.append(["SPARK_MASTER_IP", "spark-master-{execution_id}"])
    return proc


def spark_worker_proc(count: int, mem_limit: int, cores: int, image: str) -> list:
    ret = []
    for i in range(count):
        proc = ZoeApplicationProcess()
        proc.name = "spark-worker-{}".format(i)
        proc.docker_image = image
        proc.monitor = False
        proc.required_resources["memory"] = mem_limit
        port = ZoeProcessEndpoint()
        port.name = "Spark worker web interface"
        port.protocol = "http"
        port.port_number = 8081
        port.path = "/"
        port.is_main_endpoint = False
        proc.ports.append(port)
        proc.environment.append(["SPARK_WORKER_CORES", str(cores)])
        proc.environment.append(["SPARK_WORKER_RAM", str(mem_limit)])
        proc.environment.append(["SPARK_MASTER_IP", "spark-master-{execution_id}"])
        ret.append(proc)
    return ret


def spark_notebook_proc(mem_limit: int, image: str, spark_options: str) -> ZoeApplicationProcess:
    proc = ZoeApplicationProcess()
    proc.name = "spark-notebook"
    proc.docker_image = image
    proc.monitor = True
    proc.required_resources["memory"] = mem_limit
    port_app = ZoeProcessEndpoint()
    port_app.name = "Spark application web interface"
    port_app.protocol = "http"
    port_app.port_number = 4040
    port_app.path = "/"
    port_app.is_main_endpoint = False
    proc.ports.append(port_app)
    port_nb = ZoeProcessEndpoint()
    port_nb.name = "Spark Notebook interface"
    port_nb.protocol = "http"
    port_nb.port_number = 9000
    port_nb.path = "/"
    port_nb.is_main_endpoint = True
    proc.ports.append(port_nb)
    proc.environment.append(["SPARK_MASTER_IP", "spark-master-{execution_id}"])
    proc.environment.append(["SPARK_OPTIONS", spark_options])
    proc.environment.append(["SPARK_EXECUTOR_RAM", str(mem_limit)])
    return proc


def spark_notebook_app(name: str,
                       master_mem_limit: int,
                       worker_count: int,
                       worker_mem_limit: int,
                       worker_cores: int,
                       master_image: str,
                       worker_image: str,
                       notebook_image: str,
                       spark_options: str) -> ZoeApplication:
    app = ZoeApplication()
    app.name = name
    app.will_end = False
    app.priority = 512
    app.requires_binary = False
    master = spark_master_proc(master_mem_limit, master_image)
    app.processes.append(master)
    workers = spark_worker_proc(worker_count, worker_mem_limit, worker_cores, worker_image)
    app.processes += workers
    notebook = spark_notebook_proc(worker_mem_limit, notebook_image, spark_options)
    app.processes.append(notebook)
    return app


def spark_submit_proc(mem_limit: int, image: str, command: str, spark_options: str):
    proc = ZoeApplicationProcess()
    proc.name = "spark-submit"
    proc.docker_image = image
    proc.monitor = True
    proc.required_resources["memory"] = mem_limit
    port_app = ZoeProcessEndpoint()
    port_app.name = "Spark application web interface"
    port_app.protocol = "http"
    port_app.port_number = 4040
    port_app.path = "/"
    port_app.is_main_endpoint = False
    proc.ports.append(port_app)
    proc.environment.append(["SPARK_MASTER_IP", "spark-master-{execution_id}"])
    proc.environment.append(["SPARK_OPTIONS", spark_options])
    proc.environment.append(["SPARK_EXECUTOR_RAM", str(mem_limit)])
    proc.environment.append(["APPLICATION_URL", "{application_binary_url}"])
    proc.command = command
    return proc


def spark_submit_app(name: str,
                     master_mem_limit: int,
                     worker_count: int,
                     worker_mem_limit: int,
                     worker_cores: int,
                     master_image: str,
                     worker_image: str,
                     submit_image: str,
                     commandline: str,
                     spark_options: str) -> ZoeApplication:
    app = ZoeApplication()
    app.name = name
    app.will_end = False
    app.priority = 512
    app.requires_binary = False
    master = spark_master_proc(master_mem_limit, master_image)
    app.processes.append(master)
    workers = spark_worker_proc(worker_count, worker_mem_limit, worker_cores, worker_image)
    app.processes += workers
    submit = spark_submit_proc(worker_mem_limit, submit_image, commandline, spark_options)
    app.processes.append(submit)
    return app


def spark_ipython_notebook_proc(mem_limit: int, image: str, spark_options: str) -> ZoeApplicationProcess:
    proc = ZoeApplicationProcess()
    proc.name = "spark-ipython"
    proc.docker_image = image
    proc.monitor = True
    proc.required_resources["memory"] = mem_limit
    port_app = ZoeProcessEndpoint()
    port_app.name = "Spark application web interface"
    port_app.protocol = "http"
    port_app.port_number = 4040
    port_app.path = "/"
    port_app.is_main_endpoint = False
    proc.ports.append(port_app)
    port_nb = ZoeProcessEndpoint()
    port_nb.name = "iPython Notebook interface"
    port_nb.protocol = "http"
    port_nb.port_number = 8888
    port_nb.path = "/"
    port_nb.is_main_endpoint = True
    proc.ports.append(port_nb)
    proc.environment.append(["SPARK_MASTER_IP", "spark-master-{execution_id}"])
    proc.environment.append(["SPARK_OPTIONS", spark_options])
    proc.environment.append(["SPARK_EXECUTOR_RAM", str(mem_limit)])
    return proc


def spark_ipython_notebook_app(name: str,
                               master_mem_limit: int,
                               worker_count: int,
                               worker_mem_limit: int,
                               worker_cores: int,
                               master_image: str,
                               worker_image: str,
                               notebook_image: str,
                               spark_options: str) -> ZoeApplication:
    app = ZoeApplication()
    app.name = name
    app.will_end = False
    app.priority = 512
    app.requires_binary = False
    master = spark_master_proc(master_mem_limit, master_image)
    app.processes.append(master)
    workers = spark_worker_proc(worker_count, worker_mem_limit, worker_cores, worker_image)
    app.processes += workers
    notebook = spark_ipython_notebook_proc(worker_mem_limit, notebook_image, spark_options)
    app.processes.append(notebook)
    return app
