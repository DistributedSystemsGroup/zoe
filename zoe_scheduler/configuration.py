from configparser import ConfigParser

config_paths = [
    'zoe.conf',
    'zoe-scheduler.conf',
    '/etc/zoe/zoe.conf',
    '/etc/zoe/zoe-scheduler.conf'
]

defaults = {
    'zoe_scheduler': {
        'swarm_manager_url': 'tcp://swarm.example.com:2380',
        'docker_private_registry': '10.1.0.1:5000',
        'status_refresh_interval': 10,
        'check_terminated_interval': 30,
        'db_connect': 'mysql+mysqlconnector://zoe:pass@dbhost/zoe',
        'storage_path': "/var/lib/zoe/history",
        'http_listen_address': '127.0.0.1',
        'http_listen_port': 4390,
        'ipc_listen_address': '127.0.0.1',
        'ipc_listen_port': 8723
    }
}

_zoeconf = None


class ZoeSchedulerConfig(ConfigParser):
    def __init__(self):
        super().__init__(interpolation=None)
        self.read_dict(defaults)

    @staticmethod
    def write_defaults(cls, fp):
        tmp = cls()
        tmp.write(fp)

    @property
    def storage_path(self) -> str:
        return self.get('zoe_scheduler', 'storage_path')

    @property
    def check_terminated_interval(self) -> int:
        return self.getint('zoe_scheduler', 'check_terminated_interval')

    @property
    def db_url(self) -> str:
        return self.get('zoe_scheduler', 'db_connect')

    @property
    def status_refresh_interval(self) -> int:
        return self.getint('zoe_scheduler', 'status_refresh_interval')

    @property
    def docker_swarm_manager(self) -> str:
        return self.get('zoe_scheduler', 'swarm_manager_url')

    @property
    def docker_private_registry(self) -> str:
        return self.get('zoe_scheduler', 'docker_private_registry')

    @property
    def http_listen_port(self) -> int:
        return self.getint('zoe_scheduler', 'http_listen_port')

    @property
    def http_listen_address(self) -> str:
        return self.get('zoe_scheduler', 'http_listen_address')

    @property
    def ipc_listen_port(self) -> int:
        return self.getint('zoe_scheduler', 'ipc_listen_port')

    @property
    def ipc_listen_address(self) -> str:
        return self.get('zoe_scheduler', 'ipc_listen_address')


def init(config_file=None) -> ZoeSchedulerConfig:
    global _zoeconf
    _zoeconf = ZoeSchedulerConfig()
    if config_file is None:
        _zoeconf.read(config_paths)
    else:
        _zoeconf.read_file(open(config_file))
    return _zoeconf


def scheduler_conf() -> ZoeSchedulerConfig:
    return _zoeconf
