#!/usr/bin/env python3

"""
Keep the Zoe scheduler loaded with BOINC clients.

Usage: boinc_load.py <zapp_json_file>
"""

import json
import os
import sys
import time
import random

from zoe_lib.statistics import ZoeStatisticsAPI
from zoe_lib.executions import ZoeExecutionsAPI

TARGET_QUEUE_LENGTH = 10
TOTAL_JOBS = 1000
MAX_TO_START_PER_LOOP = 30


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
    print('Scheduler queue length: {}'.format(sched['queue_length']))
    return sched['queue_length']


def load_zapp(filename):
    """Loads and parses the ZApp json file."""
    return json.load(open(filename, 'r'))


def submit_zapp(zapp):
    """Submits one ZApp for execution."""
    exec_api = ZoeExecutionsAPI(zoe_url(), zoe_user(), zoe_pass())
    ret = exec_api.start('boinc-loader', zapp)
    print("Application scheduled successfully with ID {}".format(ret))


def count_jobs():
    """Count how many zapps have already been submitted."""
    exec_api = ZoeExecutionsAPI(zoe_url(), zoe_user(), zoe_pass())
    execs = exec_api.list()
    count = 0
    for e_id in execs:
        e = exec_api.get(e_id)
        if e['name'] != 'boinc-loader' or e['status'] != 'terminated':
            continue
        else:
            count += 1
    return count


def main():
    """Main."""
    zapps_to_start = TOTAL_JOBS - count_jobs()
    print('I need to start {} zapps'.format(zapps_to_start))
    zapp = load_zapp(sys.argv[1])
    while zapps_to_start > 0:
        queue_length = check_queue_length()
        if queue_length >= TARGET_QUEUE_LENGTH:
            to_sleep = random.randint(10, 300)
            print("Target scheduler queue length reached, sleeping for {} seconds".format(to_sleep))
            time.sleep(to_sleep)
            continue
        to_start_now = random.randint(1, MAX_TO_START_PER_LOOP)
        print('Will submit {} new zapps'.format(to_start_now))
        for i in range(to_start_now):
            submit_zapp(zapp)
            zapps_to_start -= 1
    print('All Zapps submitted, my work is done.')

if __name__ == "__main__":
    main()
