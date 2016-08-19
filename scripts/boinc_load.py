#!/usr/bin/env python3

"""
Keep the Zoe scheduler loaded with BOINC clients.

Usage: boinc_load.py <zapp_json_file>
"""

import csv
import json
import os
import sys
import time
import random

from zoe_lib.statistics import ZoeStatisticsAPI
from zoe_lib.executions import ZoeExecutionsAPI

TARGET_QUEUE_LENGTH = 10
NUMBER_OF_HOSTS = 10
ZAPP_PER_HOST = 4
TOTAL_JOBS = NUMBER_OF_HOSTS * ZAPP_PER_HOST
# TOTAL_JOBS = 1000
MAX_TO_START_PER_LOOP = 10


def zoe_url():
    """Gets the API URL."""
    return os.environ['ZOE_URL']


def zoe_user():
    """Gets the API user name."""
    return os.environ['ZOE_USER']


def zoe_pass():
    """Gets the API password."""
    return os.environ['ZOE_PASS']


def check_queue_length():
    """Checks how many zapps are in the scheduler queue."""
    stats_api = ZoeStatisticsAPI(zoe_url(), zoe_user(), zoe_pass())
    sched = stats_api.scheduler()
#    print('Scheduler queue length: {}'.format(sched['queue_length']))
    return sched['queue_length']


def load_zapp(filename):
    """Loads and parses the ZApp json file."""
    return json.load(open(filename, 'r'))


def submit_zapp(zapp):
    """Submits one ZApp for execution."""
    exec_api = ZoeExecutionsAPI(zoe_url(), zoe_user(), zoe_pass())
    ret = exec_api.start('boinc-loader', zapp)
    return ret


def count_jobs():
    """Count how many zapps have already been submitted."""
    exec_api = ZoeExecutionsAPI(zoe_url(), zoe_user(), zoe_pass())
    execs = exec_api.list()
    count = 0
    for e_id in execs:
        e = exec_api.get(e_id)
        if e['name'] != 'boinc-loader':
            continue
        if e['status'] != 'terminated':
            count += 1
    return count


def delete_finished():
    """Delete finished executions from Zoe."""
    exec_api = ZoeExecutionsAPI(zoe_url(), zoe_user(), zoe_pass())
    execs = exec_api.list()
    for e_id in execs:
        e = exec_api.get(e_id)
        if e['name'] == 'boinc-loader' and e['status'] == 'terminated':
            print('Execution {} has finished, deleting...'.format(e_id))
            exec_api.delete(e['id'])


def start_batches(zapp, log):
    zapps_to_start = TOTAL_JOBS - count_jobs()
    print('I need to start {} zapps'.format(zapps_to_start))
    while zapps_to_start > 0:
        queue_length = check_queue_length()
        if queue_length >= TARGET_QUEUE_LENGTH:
            to_sleep = random.randint(1, 60)
            print("Target scheduler queue length reached, sleeping for {} seconds".format(to_sleep))
            time.sleep(to_sleep)
            continue
        to_start_now = random.randint(1, MAX_TO_START_PER_LOOP)
        print('Will submit {} new zapps'.format(to_start_now))
        for i in range(to_start_now):
            zapp_id = submit_zapp(zapp)
            zapps_to_start -= 1
            print("ZApp submitted with ID {}, queue length {}, {} zapps to go".format(zapp_id, queue_length, zapps_to_start))
            log.writerow({'zapp_id': zapp_id, 'queue_length': queue_length})


def start_continuous(zapp, log):
    zapps_to_start = TOTAL_JOBS - count_jobs()
    print('I need to start {} zapps'.format(zapps_to_start))
    while zapps_to_start > 0:
        zapp_id = submit_zapp(zapp)
        zapps_to_start -= 1
        time_to_sleep = random.uniform(0, 1)
        queue_length = check_queue_length()
        print("ZApp submitted with ID {}, queue length {}, will sleep for {}, {} zapps to go".format(zapp_id, queue_length, time_to_sleep, zapps_to_start))
        log.writerow({'zapp_id': zapp_id, 'queue_length': queue_length})
        time.sleep(time_to_sleep)


def keep_some_running(zapp):
    while True:
        zapps_to_start = TOTAL_JOBS - count_jobs()
        print('I need to start {} zapps'.format(zapps_to_start))
        if zapps_to_start > 0:
            for i in range(zapps_to_start):
                queue_length = check_queue_length()
                zapp_id = submit_zapp(zapp)
                print("ZApp submitted with ID {}, queue length {}, {} zapps to go".format(zapp_id, queue_length, zapps_to_start))
        try:
            print('Sleeping')
            time.sleep(60)
        except KeyboardInterrupt:
            print('Exiting infinite loop')
            break
        delete_finished()


def main():
    """Main."""
    log_fieldnames = ['zapp_id', 'queue_length']
    log = csv.DictWriter(open('run.csv', 'w'), fieldnames=log_fieldnames)
    log.writeheader()
    zapp = load_zapp(sys.argv[1])
    # start_batches(zapp, log)
    # start_continuous(zapp, log)
    keep_some_running(zapp)

    print('All Zapps submitted, my work is done.')

if __name__ == "__main__":
    main()
