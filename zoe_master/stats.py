# Copyright (c) 2015, Daniele Venzano
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


class Stats:
    def __init__(self):
        self.timestamp = None

    def to_dict(self) -> dict:
        ret = {}
        ret.update(vars(self))
        return ret


class SwarmNodeStats(Stats):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.docker_endpoint = None
        self.container_count = 0
        self.cores_total = 0
        self.cores_reserved = 0
        self.memory_total = 0
        self.memory_reserved = 0
        self.labels = {}


class SwarmStats(Stats):
    def __init__(self):
        super().__init__()
        self.container_count = 0
        self.image_count = 0
        self.memory_total = 0
        self.cores_total = 0
        self.placement_strategy = ''
        self.active_filters = []
        self.status = 'Unknown'
        self.nodes = []

    def to_dict(self) -> dict:
        ret = {
            'container_count': self.container_count,
            'image_count': self.image_count,
            'memory_total': self.memory_total,
            'cores_total': self.cores_total,
            'placement_strategy': self.placement_strategy,
            'active_filters': self.active_filters,
            'nodes': []
        }
        for node in self.nodes:
            ret['nodes'].append(node.to_dict())

        return ret


class SchedulerStats(Stats):
    def __init__(self):
        super().__init__()
        self.count_waiting = 0
        self.waiting_list = []


class ContainerStats(Stats):
    def __init__(self, docker_stats):
        super().__init__()
#        self.docker_stats = docker_stats
#        self.blkio_serviced_ops_read = sum([x['value'] for x in docker_stats['blkio_stats']['io_serviced_recursive'] if x['op'] == 'Read'])
#        self.blkio_serviced_ops_write = sum([x['value'] for x in docker_stats['blkio_stats']['io_serviced_recursive'] if x['op'] == 'Write'])
#        self.blkio_serviced_ops_async = sum([x['value'] for x in docker_stats['blkio_stats']['io_serviced_recursive'] if x['op'] == 'Async'])
#        self.blkio_serviced_ops_sync = sum([x['value'] for x in docker_stats['blkio_stats']['io_serviced_recursive'] if x['op'] == 'Sync'])
#        self.blkio_serviced_ops_total = sum([x['value'] for x in docker_stats['blkio_stats']['io_serviced_recursive'] if x['op'] == 'Total'])

        self.io_bytes_read = sum([x['value'] for x in docker_stats['blkio_stats']['io_service_bytes_recursive'] if x['op'] == 'Read'])
        self.io_bytes_write = sum([x['value'] for x in docker_stats['blkio_stats']['io_service_bytes_recursive'] if x['op'] == 'Write'])
#        self.blkio_serviced_bytes_async = sum([x['value'] for x in docker_stats['blkio_stats']['io_service_bytes_recursive'] if x['op'] == 'Async'])
#        self.blkio_serviced_bytes_sync = sum([x['value'] for x in docker_stats['blkio_stats']['io_service_bytes_recursive'] if x['op'] == 'Sync'])
#        self.blkio_serviced_bytes_total = sum([x['value'] for x in docker_stats['blkio_stats']['io_service_bytes_recursive'] if x['op'] == 'Total'])

        self.memory_used = docker_stats['memory_stats']['usage']
        self.memory_total = docker_stats['memory_stats']['limit']

        self.net_ifaces = docker_stats['networks']

# documentation_sample = {
#     {
#         'cpu_stats': {
#             'throttling_data': {
#                 'periods': 0,
#                 'throttled_periods': 0,
#                 'throttled_time': 0
#             },
#             'system_cpu_usage': 65875968520000000,
#             'cpu_usage': {
#                 'percpu_usage': [
#                     736438148,
#                     831366317,
#                     447071507,
#                     1013685525,
#                     1737636976,
#                     183319803,
#                     1028588050,
#                     209580806,
#                     682154523,
#                     273060494,
#                     372253571,
#                     135631151,
#                     411354030,
#                     198948083,
#                     563605935,
#                     121068036,
#                     84158335,
#                     0,
#                     18378122,
#                     23639063,
#                     12823232,
#                     8058874,
#                     129998083,
#                     10754519,
#                     32123630,
#                     39068838,
#                     30947971,
#                     21593132,
#                     232865974,
#                     129752271,
#                     23814073,
#                     199014665
#                 ],
#                 'total_usage': 9942753737,
#                 'usage_in_kernelmode': 1840000000,
#                 'usage_in_usermode': 9420000000
#             }
#         },
#         'memory_stats': {
#             'usage': 273829888,
#             'limit': 8589934592,
#             'failcnt': 0,
#             'max_usage': 274112512,
#             'stats': {
#                 'pgmajfault': 0,
#                 'total_pgpgout': 18635,
#                 'active_file': 0,
#                 'total_rss_huge': 226492416,
#                 'writeback': 0,
#                 'inactive_file': 32768,
#                 'total_rss': 272175104,
#                 'cache': 90112,
#                 'rss': 272175104,
#                 'total_pgmajfault': 0,
#                 'total_inactive_anon': 20480,
#                 'active_anon': 272183296,
#                 'total_pgfault': 57405,
#                 'pgpgin': 29918,
#                 'pgfault': 57405,
#                 'rss_huge': 226492416,
#                 'unevictable': 0,
#                 'total_writeback': 0,
#                 'total_unevictable': 0,
#                 'total_inactive_file': 32768,
#                 'total_pgpgin': 29918,
#                 'total_active_file': 0,
#                 'total_mapped_file': 32768,
#                 'mapped_file': 32768,
#                 'inactive_anon': 20480,
#                 'hierarchical_memory_limit': 8589934592,
#                 'pgpgout': 18635,
#                 'total_active_anon': 272183296,
#                 'total_cache': 90112
#             }
#         },
#         'blkio_stats': {
#             'io_service_bytes_recursive': [
#                 {
#                     'minor': 16,
#                     'value': 0,
#                     'major': 8,
#                     'op': 'Read'
#                 }, {
#                     'minor': 16,
#                     'value': 0,
#                     'major': 8,
#                     'op': 'Write'
#                 }, {
#                     'minor': 16,
#                     'value': 0,
#                     'major': 8,
#                     'op': 'Sync'
#                 }, {
#                     'minor': 16,
#                     'value': 0,
#                     'major': 8,
#                     'op': 'Async'
#                 }, {
#                     'minor': 16,
#                     'value': 0,
#                     'major': 8,
#                     'op': 'Total'
#                 }, {
#                     'minor': 1,
#                     'value': 0,
#                     'major': 252,
#                     'op': 'Read'
#                 }, {
#                     'minor': 1,
#                     'value': 0,
#                     'major': 252,
#                     'op': 'Write'
#                 }, {
#                     'minor': 1,
#                     'value': 0,
#                     'major': 252,
#                     'op': 'Sync'
#                 }, {
#                     'minor': 1,
#                     'value': 0,
#                     'major': 252,
#                     'op': 'Async'
#                 }, {
#                     'minor': 1,
#                     'value': 0,
#                     'major': 252,
#                     'op': 'Total'
#                 }
#             ],
#             'io_merged_recursive': [],
#             'io_serviced_recursive': [
#                 {
#                     'minor': 16,
#                     'value': 0,
#                     'major': 8,
#                     'op': 'Read'
#                 }, {
#                     'minor': 16,
#                     'value': 0,
#                     'major': 8,
#                     'op': 'Write'
#                 }, {
#                     'minor': 16,
#                     'value': 0,
#                     'major': 8,
#                     'op': 'Sync'
#                 }, {
#                     'minor': 16,
#                     'value': 0,
#                     'major': 8,
#                     'op': 'Async'
#                 }, {
#                     'minor': 16,
#                     'value': 0,
#                     'major': 8,
#                     'op': 'Total'
#                 }, {
#                     'minor': 1,
#                     'value': 0,
#                     'major': 252,
#                     'op': 'Read'
#                 }, {
#                     'minor': 1,
#                     'value': 0,
#                     'major': 252,
#                     'op': 'Write'
#                 }, {
#                     'minor': 1,
#                     'value': 0,
#                     'major': 252,
#                     'op': 'Sync'
#                 }, {
#                     'minor': 1,
#                     'value': 0,
#                     'major': 252,
#                     'op': 'Async'
#                 }, {
#                     'minor': 1,
#                     'value': 0,
#                     'major': 252,
#                     'op': 'Total'
#                 }
#             ],
#             'io_wait_time_recursive': [],
#             'io_service_time_recursive': [],
#             'io_time_recursive': [],
#             'sectors_recursive': [],
#             'io_queue_recursive': []
#         },
#         'networks': {
#             'eth1': {
#                 'tx_bytes': 980,
#                 'rx_dropped': 0,
#                 'rx_errors': 0,
#                 'rx_bytes': 1720,
#                 'tx_dropped': 0,
#                 'rx_packets': 18,
#                 'tx_packets': 13,
#                 'tx_errors': 0
#             },
#             'eth0': {
#                 'tx_bytes': 63221,
#                 'rx_dropped': 0,
#                 'rx_errors': 0,
#                 'rx_bytes': 7244,
#                 'tx_dropped': 0,
#                 'rx_packets': 87,
#                 'tx_packets': 79,
#                 'tx_errors': 0
#             }
#         },
#         'precpu_stats': {
#             'throttling_data': {
#                 'periods': 0,
#                 'throttled_periods': 0,
#                 'throttled_time': 0
#             },
#             'system_cpu_usage': 0,
#             'cpu_usage': {
#                 'percpu_usage': None,
#                 'total_usage': 0,
#                 'usage_in_kernelmode': 0,
#                 'usage_in_usermode': 0
#             }
#         },
#         'read': '2016-02-04T14:41:21.325853434+01:00'
#     }
#}
