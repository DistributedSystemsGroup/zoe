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

import zoe_lib.config as config
import zoe_api.db_init

config.load_configuration()

zoe_api.db_init.init()
