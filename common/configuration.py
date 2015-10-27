from configparser import ConfigParser

config_paths = [
    'zoe.conf',
    '/etc/zoe/zoe.conf',
]

defaults = {
    'common': {
        'object_storage_url': 'http://localhost:4390'
    },
    'zoe_client': {
        'db_connect': 'mysql+mysqlconnector://zoe:pass@dbhost/zoe',
        'scheduler_ipc_address': 'localhost',
        'scheduler_ipc_port': 8723,
    },
    'zoe_web': {
        'smtp_server': 'smtp.exmaple.com',
        'smtp_user': 'zoe@exmaple.com',
        'smtp_password': 'changeme',
        'cookie_secret': b"\xc3\xb0\xa7\xff\x8fH'\xf7m\x1c\xa2\x92F\x1d\xdcz\x05\xe6CJN5\x83!",
        'web_server_name': 'localhost'
    },
    'zoe_scheduler': {
        'swarm_manager_url': 'tcp://swarm.example.com:2380',
        'docker_private_registry': '10.1.0.1:5000',
        'status_refresh_interval': 10,
        'check_terminated_interval': 30,
        'db_connect': 'mysql+mysqlconnector://zoe:pass@dbhost/zoe',
        'ipc_listen_address': '127.0.0.1',
        'ipc_listen_port': 8723,
        'ddns_keyfile': '/path/to/rndc.key',
        'ddns_server': '127.0.0.1',
        'ddns_domain': 'swarm.example.com'
    }
}

_zoeconf = None


class ZoeConfig(ConfigParser):
    def __init__(self):
        super().__init__(interpolation=None)
        self.read_dict(defaults)

    @staticmethod
    def write_defaults(cls, fp):
        tmp = cls()
        tmp.write(fp)

    @property
    def db_url(self) -> str:
        return self.get('zoe_client', 'db_connect')

    @property
    def ipc_server(self) -> str:
        return self.get('zoe_client', 'scheduler_ipc_address')

    @property
    def ipc_port(self) -> int:
        return self.getint('zoe_client', 'scheduler_ipc_port')

    @property
    def object_storage_url(self) -> str:
        return self.get('common', 'object_storage_url')

    @property
    def web_server_name(self) -> str:
        return self.get('zoe_web', 'web_server_name')

    @property
    def smtp_server(self) -> str:
        return self.get('zoe_web', 'smtp_server')

    @property
    def smtp_user(self) -> str:
        return self.get('zoe_web', 'smtp_user')

    @property
    def smtp_password(self) -> str:
        return self.get('zoe_web', 'smtp_password')

    @property
    def cookies_secret_key(self):
        return self.get('zoe_web', 'cookie_secret')

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
    def ipc_listen_port(self) -> int:
        return self.getint('zoe_scheduler', 'ipc_listen_port')

    @property
    def ipc_listen_address(self) -> str:
        return self.get('zoe_scheduler', 'ipc_listen_address')

    @property
    def ddns_keyfile(self) -> str:
        return self.get('zoe_scheduler', 'ddns_keyfile')

    @property
    def ddns_server(self) -> str:
        return self.get('zoe_scheduler', 'ddns_server')

    @property
    def ddns_domain(self) -> str:
        return self.get('zoe_scheduler', 'ddns_domain')


def conf_init(config_file=None) -> ZoeConfig:
    global _zoeconf
    _zoeconf = ZoeConfig()
    if config_file is None:
        _zoeconf.read(config_paths)
    else:
        _zoeconf.read_file(open(config_file))
    return _zoeconf


def zoe_conf() -> ZoeConfig:
    return _zoeconf
