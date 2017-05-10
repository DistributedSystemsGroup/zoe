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

"""
This module contains the Zoe Info API.
"""

import logging

from zoe_lib.api_base import ZoeAPIBase

log = logging.getLogger(__name__)


class ZoeValidationAPI(ZoeAPIBase):
    """
    The Info API class. This API exports static information about Zoe, versions and configuration.
    """
    def validate(self, application_description):
        """
        Queries Zoe for versions and local configuration parameters.

        :return:
        """
        zapp = {
            "application": application_description,
        }
        data_, status_code = self._rest_post('/zapp_validate', zapp)
        if status_code != 200:
            return False
        else:
            return True
