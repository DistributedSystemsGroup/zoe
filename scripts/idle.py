#!/usr/bin/env python3

"""
Keep the Zoe scheduler loaded with BOINC clients.

Usage: boinc_load.py <zapp_json_file>
"""

import json
import sys
import time
import random
import collections
import glob
import os

from zoe_cmd.utils import read_auth
from zoe_cmd.api_lib import ZoeAPI

TOTAL_JOBS = 1000
USAGE_WATERMARK = 0.4
USAGE_HYSTERESIS = 0.1
BATCH_SIZE_TO_KILL = 5
EXECUTION_NAME = 'idle-loader'


def check_queue_length(api):
    """Checks how many zapps are in the scheduler queue."""
    sched = api.statistics.scheduler()
#    print('Scheduler queue length: {}'.format(sched['queue_length']))
    return sched['queue_length']


def platform_usage(api):
    """Calculate the platform load."""
    sched = api.statistics.scheduler()
    core_total = sched['platform_stats']['cores_total']
    memory_total = sched['platform_stats']['memory_total']
    core_reserved = 0
    memory_reserved = 0
    for node in sched['platform_stats']['nodes']:
        core_reserved += node['cores_reserved']
        memory_reserved += node['memory_reserved']
    core_usage = core_reserved / core_total
    memory_usage = memory_reserved / memory_total
    return max(core_usage, memory_usage)


def load_zapp(filename):
    """Loads and parses the ZApp json file."""
    return json.load(open(filename, 'r'))


def submit_zapp(zapps, name, api):
    """Submits one ZApp for execution."""
    zapp = random.choice(zapps)
    ret = api.executions.start(name, zapp)
    return ret


def terminate_zapp(exec_id, api):
    """Terminate a running zapp execution."""
    api.executions.terminate(exec_id)


def list_jobs(api, name):
    """List zapps that have already been submitted."""
    execs = api.executions.list(status='submitted', name=name)
    execs += api.executions.list(status='queued', name=name)
    execs += api.executions.list(status='starting', name=name)
    execs += api.executions.list(status='running', name=name)
    execs = [e['id'] for e in execs]
    return execs


def count_jobs(api, name, all=False):
    """Count how many zapps have already been submitted."""
    if all:
        sched = api.statistics.scheduler()
        return sched['running_length']
    execs = api.executions.list(status='submitted', name=name)
    execs += api.executions.list(status='queued', name=name)
    execs += api.executions.list(status='starting', name=name)
    execs += api.executions.list(status='running', name=name)
    return len(execs)


def keep_some_running(zapps, exec_name, api):
    """Loop and start or kill executions depending on platform load."""
    old_queue_length = 0
    while True:
        print(time.ctime())
        currently_running = list_jobs(api, exec_name)
        usage = platform_usage(api)
        state = "steady"
        queuing = False

        queue_length = check_queue_length(api)
        if queue_length == 0:
            queuing = False
        if queue_length > 0 and old_queue_length == 0:
            queuing = False
        if queue_length > 0 and old_queue_length > 0:
            queuing = True
        old_queue_length = queue_length

        if not queuing and usage < (USAGE_WATERMARK - USAGE_HYSTERESIS):
            state = "grow"
        if (queuing or usage > (USAGE_WATERMARK + USAGE_HYSTERESIS)) and len(currently_running) > 0:
            state = "shrink"

        if state == "grow":
            while usage <= USAGE_WATERMARK:
                print("Platform usage is {:.2f}, can start one more".format(usage))
                zapp_id = submit_zapp(zapps, exec_name, api)
                print("ZApp submitted with ID {}".format(zapp_id))
                time.sleep(5)
                queue_length = check_queue_length(api)
                if queue_length > 0:
                    old_queue_length = queue_length
                    time.sleep(30)
                    break
                usage = platform_usage(api)
                continue
        elif state == "shrink":
            while usage > USAGE_WATERMARK:
                print("Platform usage is {} (target {}), terminating some executions".format(queue_length, usage, USAGE_WATERMARK - USAGE_HYSTERESIS))
                if 0 < len(currently_running) <= BATCH_SIZE_TO_KILL:
                    to_kill = currently_running
                else:
                    to_kill = currently_running.sort()[-5:]
                print("Terminating {}".format(to_kill))
                for exec_id in to_kill:
                    terminate_zapp(exec_id, api)
                print("Sleeping 30 seconds")
                time.sleep(30)
                currently_running = list_jobs(api, exec_name)
                queue_length = check_queue_length(api)
                usage = platform_usage(api)
                if queue_length > 0:
                    old_queue_length = queue_length
                    time.sleep(30)
                    break
        elif state == "steady":
            print("Platform usage is {:.2f}, with {} running zapps, sleeping".format(usage, len(currently_running)))
            time.sleep(60)


Args = collections.namedtuple('Args', ['auth_file'])


def main():
    """Main."""
    fauth = os.path.join(os.getenv('HOME'), '.zoerc')
    args = Args(fauth)
    auth = read_auth(args)
    api = ZoeAPI(auth['url'], auth['user'], auth['pass'])
    zapps = []
    for zapp_file in glob.glob(sys.argv[1] + '/*.json'):
        zapps.append(load_zapp(zapp_file))
    try:
        keep_some_running(zapps, EXECUTION_NAME, api)
    except KeyboardInterrupt:
        print('Exiting')

    print('All Zapps submitted, my work is done.')


if __name__ == "__main__":
    main()
