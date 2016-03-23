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

from zoe_lib.predefined_apps.copier import copier_app
from zoe_lib.predefined_apps.spark_interactive import spark_jupyter_notebook_app
from zoe_lib.predefined_apps.eurecom_aml_lab import spark_jupyter_notebook_lab_app
from zoe_lib.predefined_apps.hdfs import hdfs_app
from zoe_lib.predefined_apps.openmpi import openmpi_app
from zoe_lib.predefined_apps.spark_submit import spark_submit_app
from zoe_lib.predefined_apps.test_sleep import sleeper_app

PREDEFINED_APPS = [
    copier_app,
    spark_jupyter_notebook_app,
    spark_jupyter_notebook_lab_app,
    hdfs_app,
    openmpi_app,
    spark_submit_app,
    sleeper_app
]
