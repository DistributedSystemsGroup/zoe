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
        self.count_running = 0
        self.count_waiting = 0


class PlatformStats(Stats):
    def __init__(self):
        super().__init__()
        self.swarm = SwarmStats()
        self.scheduler = SchedulerStats()

    def to_dict(self) -> dict:
        return {
            'swarm': self.swarm.to_dict(),
            'scheduler': self.scheduler.to_dict()
        }


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

        self.net_bytes_rx = docker_stats['network']['rx_bytes']
        self.net_bytes_tx = docker_stats['network']['tx_bytes']


documentation_sample = {
    'blkio_stats': {
        'io_time_recursive': [],
        'io_wait_time_recursive': [],
        'io_merged_recursive': [],
        'io_service_time_recursive': [],
        'io_serviced_recursive': [
            {'minor': 0, 'op': 'Read', 'major': 8, 'value': 0},
            {'minor': 0, 'op': 'Write', 'major': 8, 'value': 1},
            {'minor': 0, 'op': 'Sync', 'major': 8, 'value': 0},
            {'minor': 0, 'op': 'Async', 'major': 8, 'value': 1},
            {'minor': 0, 'op': 'Total', 'major': 8, 'value': 1},
            {'minor': 0, 'op': 'Read', 'major': 252, 'value': 0},
            {'minor': 0, 'op': 'Write', 'major': 252, 'value': 1},
            {'minor': 0, 'op': 'Sync', 'major': 252, 'value': 0},
            {'minor': 0, 'op': 'Async', 'major': 252, 'value': 1},
            {'minor': 0, 'op': 'Total', 'major': 252, 'value': 1}
        ],
        'io_service_bytes_recursive': [
            {'minor': 0, 'op': 'Read', 'major': 8, 'value': 0},
            {'minor': 0, 'op': 'Write', 'major': 8, 'value': 32768},
            {'minor': 0, 'op': 'Sync', 'major': 8, 'value': 0},
            {'minor': 0, 'op': 'Async', 'major': 8, 'value': 32768},
            {'minor': 0, 'op': 'Total', 'major': 8, 'value': 32768},
            {'minor': 0, 'op': 'Read', 'major': 252, 'value': 0},
            {'minor': 0, 'op': 'Write', 'major': 252, 'value': 32768},
            {'minor': 0, 'op': 'Sync', 'major': 252, 'value': 0},
            {'minor': 0, 'op': 'Async', 'major': 252, 'value': 32768},
            {'minor': 0, 'op': 'Total', 'major': 252, 'value': 32768}
        ],
        'io_queue_recursive': [],
        'sectors_recursive': []
    },
    'cpu_stats': {
        'cpu_usage': {
            'usage_in_usermode': 8380000000,
            'usage_in_kernelmode': 2630000000,
            'total_usage': 34451274609,
            'percpu_usage': [931702517, 2764976848, 928621564, 2669799012, 1117103491, 2797807324, 1278365416, 2919322388, 1195818284, 2794439644, 1105212782, 2628238214, 1018437691, 2713559369, 913142014, 2966544077, 555254965, 73830222, 129362189, 120696574, 232636452, 54415721, 71511012, 111871561, 261233403, 736167553, 61198008, 713285344, 41359796, 287955073, 78816569, 178589532]},
        'throttling_data': {
            'throttled_periods': 0,
            'throttled_time': 0,
            'periods': 0
        }, 'system_cpu_usage': 4257821208713451
    },
    'memory_stats': {
        'usage': 249561088,
        'limit': 2147483648,
        'stats': {
            'total_inactive_anon': 12288,
            'pgfault': 75899,
            'inactive_file': 32768,
            'total_rss': 249479168,
            'total_writeback': 0,
            'total_inactive_file': 32768,
            'writeback': 0,
            'total_pgmajfault': 0,
            'active_file': 0,
            'total_pgfault': 75899,
            'hierarchical_memory_limit': 2147483648,
            'total_active_file': 0,
            'total_pgpgout': 34070,
            'pgpgout': 34070,
            'total_rss_huge': 195035136,
            'total_cache': 81920,
            'total_mapped_file': 32768,
            'total_pgpgin': 47475,
            'rss_huge': 195035136,
            'unevictable': 0,
            'total_unevictable': 0,
            'rss': 249479168,
            'total_active_anon': 249499648,
            'cache': 81920,
            'active_anon': 249499648,
            'inactive_anon': 12288,
            'pgpgin': 47475,
            'mapped_file': 32768,
            'pgmajfault': 0
        },
        'max_usage': 266846208,
        'failcnt': 0
    },
    'network': {
        'rx_packets': 1214,
        'rx_bytes': 308646,
        'tx_dropped': 0,
        'rx_dropped': 0,
        'tx_errors': 0,
        'tx_bytes': 61784,
        'rx_errors': 0,
        'tx_packets': 1019
    },
    'precpu_stats': {
        'cpu_usage': {
            'usage_in_usermode': 0,
            'usage_in_kernelmode': 0,
            'total_usage': 0,
            'percpu_usage': None
        },
        'throttling_data': {
            'throttled_periods': 0,
            'throttled_time': 0,
            'periods': 0
        },
        'system_cpu_usage': 0
    },
    'read': '2015-09-09T14:52:19.254587126+02:00'
}
