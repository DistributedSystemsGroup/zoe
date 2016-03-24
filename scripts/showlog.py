#!/usr/bin/python3

import sys
import argparse

from kafka import KafkaConsumer

parser = argparse.ArgumentParser(description='Zoe Kafka log viewer')
parser.add_argument('kafka_address', help='Address of the Kafka broker')
parser.add_argument('--list-logs', action='store_true', help='List all the available service logs')
parser.add_argument('--topic', help='Service name to fetch and monitor for activity')

args = parser.parse_args()

consumer = KafkaConsumer(bootstrap_servers=args.kafka_address)

if args.list_logs:
    for topic in consumer.topics():
        if topic[0] != '_':
            print(topic)
    sys.exit(0)

consumer.subscribe(pattern=args.topic)
consumer.poll(1)
consumer.seek_to_beginning()
try:
    for msg in consumer:
        print(msg.value.decode('utf-8'))
except KeyboardInterrupt:
    print('showlog exiting...')

