#!/usr/bin/env python3

"""
Retrieve a workload trace from boinc jobs.

Usage: boinc_trace.py <out_file>
"""

import os
import sys

import requests

from zoe_lib.statistics import ZoeStatisticsAPI
from zoe_lib.executions import ZoeExecutionsAPI

TARGET_QUEUE_LENGTH = 5
INFLUXDB_PORT = '8086'
INFLUXDB_ADDRESS = ''


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


def submit_zapp(zapp):
    """Submits one ZApp for execution."""
    exec_api = ZoeExecutionsAPI(zoe_url(), zoe_user(), zoe_pass())
    ret = exec_api.start('boinc-loader', zapp)
    print("Application scheduled successfully with ID {}, use the exec-get command to check its status".format(ret))


def get_influx_cpu_data(exec_id):
    """Get CPU data."""
    query_params = {
        'db': 'telegraf',
        'q': 'SELECT LAST(usage_total) FROM docker_container_cpu WHERE "zoe.execution.id" = \'{}\' AND cpu = \'cpu-total\''.format(exec_id)
    }
    resp = requests.get("http://" + INFLUXDB_ADDRESS + "/query", params=query_params)
    resp = resp.json()
    try:
        cpu_usage = resp['results'][0]['series'][0]['values'][0][1]
    except KeyError:
        cpu_usage = 0
    return cpu_usage


def get_influx_mem_data(exec_id):
    """Get memory data."""
    query_params = {
        'db': 'telegraf',
        'q': 'SELECT MAX(max_usage) FROM docker_container_mem WHERE "zoe.execution.id" = \'{}\''.format(exec_id)
    }
    resp = requests.get("http://" + INFLUXDB_ADDRESS + "/query", params=query_params)
    resp = resp.json()
    try:
        mem_usage = resp['results'][0]['series'][0]['values'][0][1]
    except KeyError:
        mem_usage = 0
    return mem_usage


def get_influx_net_rx_data(exec_id):
    """Get network RX data."""
    query_params = {
        'db': 'telegraf',
        'q': 'SELECT LAST(rx_bytes) FROM docker_container_net WHERE "zoe.execution.id" = \'{}\' AND network = \'eth1\''.format(exec_id)
    }
    resp = requests.get("http://" + INFLUXDB_ADDRESS + "/query", params=query_params)
    resp = resp.json()
    try:
        net_rx_usage = resp['results'][0]['series'][0]['values'][0][1]
    except KeyError:
        net_rx_usage = 0
    return net_rx_usage


def get_influx_net_tx_data(exec_id):
    """Get network TX data."""
    query_params = {
        'db': 'telegraf',
        'q': 'SELECT LAST(tx_bytes) FROM docker_container_net WHERE "zoe.execution.id" = \'{}\' AND network = \'eth1\''.format(exec_id)
    }
    resp = requests.get("http://" + INFLUXDB_ADDRESS + "/query", params=query_params)
    resp = resp.json()
    try:
        net_tx_usage = resp['results'][0]['series'][0]['values'][0][1]
    except KeyError:
        net_tx_usage = 0
    return net_tx_usage


def get_influx_blkio_data(exec_id):
    """Get disk data."""
    query_params = {
        'db': 'telegraf',
        'q': 'SELECT LAST(io_serviced_recursive_total) FROM docker_container_blkio WHERE "zoe.execution.id" = \'{}\''.format(exec_id)
    }
    resp = requests.get("http://" + INFLUXDB_ADDRESS + "/query", params=query_params)
    resp = resp.json()
    try:
        blkio_usage = resp['results'][0]['series'][0]['values'][0][1]
    except KeyError:
        blkio_usage = 0
    return blkio_usage


def main():
    """Main."""
    global INFLUXDB_ADDRESS
    exec_api = ZoeExecutionsAPI(zoe_url(), zoe_user(), zoe_pass())
    INFLUXDB_ADDRESS = sys.argv[1] + ':' + INFLUXDB_PORT
    execs = exec_api.list()
    print('id,time_submit,time_start,time_end,cpu_usage,mem_usage,net_rx_usage,net_tx_usage,blkio_usage')
    for e_id in execs:
        e = exec_api.get(e_id)
        if e['name'] != 'boinc-loader' or e['status'] != 'terminated':
            continue
        trace_line = {
            'id': e['id'],
            'time_submit': e['time_submit'],
            'time_start': e['time_start'],
            'time_end': e['time_end'],
            'cpu_usage': get_influx_cpu_data(e_id),
            'mem_usage': get_influx_mem_data(e_id),
            'net_rx_usage': get_influx_net_rx_data(e_id),
            'net_tx_usage': get_influx_net_tx_data(e_id),
            'blkio_usage': get_influx_blkio_data(e_id)
        }
        print('{id},{time_submit},{time_start},{time_end},{cpu_usage},{mem_usage},{net_rx_usage},{net_tx_usage},{blkio_usage}'.format(**trace_line))

if __name__ == "__main__":
    main()
