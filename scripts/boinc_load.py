#!/usr/bin/env python3

"""
Keep the Zoe scheduler loaded with BOINC clients.

Usage: boinc_load.py <zapp_json_file>
"""

import json
import os
import sys
import time

from zoe_lib.statistics import ZoeStatisticsAPI
from zoe_lib.executions import ZoeExecutionsAPI

TARGET_QUEUE_LENGTH = 5


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
    print("Application scheduled successfully with ID {}, use the exec-get command to check its status".format(ret))


def main():
    """Main."""
    zapp = load_zapp(sys.argv[1])
    queue_length = check_queue_length()
    while queue_length < TARGET_QUEUE_LENGTH:
        number_to_submit = TARGET_QUEUE_LENGTH - queue_length
        print('Current queue length is {}, submitting {} new zapps'.format(queue_length, number_to_submit))
        for i in range(number_to_submit):
            submit_zapp(zapp)
        time.sleep(5)
    print('Zoe scheduler target queue length reached, my work is done.')

if __name__ == "__main__":
    main()
