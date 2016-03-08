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

from zoe_lib.applications import app_validate
from zoe_lib.predefined_apps import hadoop
from zoe_lib.predefined_apps import spark


def test_from_dict(application_dict):
    app_validate(application_dict)


def test_predefined_spark():
    app = spark.spark_jupyter_notebook_app("test", 4, 3, 4, 4, 'spark-master', 'spark-worker', 'ipython')
    app_validate(app)
    app = spark.spark_submit_app("test", 4, 3, 4, 4, 'spark-master', 'spark-worker', 'spark-notebook', '--test', '')
    app_validate(app)


def test_predefined_hadoop():
    app = hadoop.hdfs_app("test", 'namenode-image', 3, 'datanode-image')
    app_validate(app)
