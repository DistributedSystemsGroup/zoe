# Copyright (c) 2017, Pace Francesco
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
import logging

from zoe_master.plugins.connectors import RabbitMQ

log = logging.getLogger(__name__)


class Crystal:
    def __init__(self, channel):
        self.channel = channel

    def transmit_policy(self, tenant, policy):
        message = "{}:{}".format(tenant, policy)
        if self.channel['protocol'] == 'rabbitmq':
            log.debug("Transmitting policy to Crystal via RabbitMQ")
            rmq = RabbitMQ(self.channel['username'], self.channel['password'], self.channel['host'])
            rmq.open_connection()
            rmq.send_message(self.channel['queue'], message)
            rmq.close_connection()
