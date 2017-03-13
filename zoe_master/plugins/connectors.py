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
import pika


log = logging.getLogger(__name__)


class RabbitMQ:
    def __init__(self, username, password, host):
        self.username = username
        self.password = password
        self.host = host
        self.channel = None

    def open_connection(self):
        log.debug("Opening connection to RabbitMQ: {}".format(self.host))
        credentials = pika.PlainCredentials(self.username, self.password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(self.host, credentials=credentials))
        self.channel = connection.channel()

    def send_message(self, exchange, queue, message):
        log.debug("Sending message to RabbitMQ. Message -> {} // Exchange -> {} // Queue -> {}".format(message, exchange, queue))
        self.channel.basic_publish(exchange=exchange,
                                   routing_key=queue,
                                   body=message)

    def close_connection(self):
        self.channel.close()
