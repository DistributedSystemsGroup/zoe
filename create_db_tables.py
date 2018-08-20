# Copyright (c) 2017, Daniele Venzano
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

"""Create the DB tables needed by Zoe. This script is used in the CI pipeline to prevent race conditions with zoe-api automatically creating the tables while zoe-master is starting at the same time."""

import sys
import time

import zoe_lib.config
import zoe_lib.state.sql_manager

zoe_lib.config.load_configuration()

print("Warning, this script will delete the database tables for the deployment '{}' before creating new ones".format(config.get_conf().deployment_name))
print("If you are installing Zoe for the first time, you have nothing to worry about")
print("Sleeping 5 seconds before continuing, hit CTRL-C to stop and think.")

try:
    time.sleep(5)
except KeyboardInterrupt:
    print("Aborted.")
    sys.exit(1)

zoe_lib.state.sql_manager.SQLManager(zoe_lib.config.get_conf()).init_db(force=True)
