from configparser import ConfigParser

ipcconf = {
    'server': None,
    'port': None,
}

config_paths = [
    'zoe.conf',
    '/etc/zoe/zoe.conf'
]

defaults = {
    'docker': {
        'swarm_manager_url': 'tcp://swarm.example.com:2380',
        'private_registry': '10.1.0.1:5000'
    },
    'intervals': {
        'status_refresh': 10,
        'scheduler_task': 10,
        'proxy_update_accesses': 300,
        'check_health': 30,
        'notebook_max_age_no_activity': 24,
        'notebook_warning_age_no_activity': 2
    },
    'db': {
        'url': 'mysql+mysqlconnector://zoe:pass@dbhost/zoe'
    },
    'apache': {
        'proxy_config_file': '/tmp/zoe-proxy.conf',
        'access_log': '/var/log/apache2/access.log',
        'web_server_name': 'bigfoot-m2.eurecom.fr',
        'proxy_path_prefix': '/proxy'
    },
    'smtp': {
        'server': 'smtp.exmaple.com',
        'user': 'zoe@exmaple.com',
        'password': 'changeme'
    },
    'filesystem': {
        'history_path': "/var/lib/zoe/history"
    },
    'flask': {
        'secret_key': b"\xc3\xb0\xa7\xff\x8fH'\xf7m\x1c\xa2\x92F\x1d\xdcz\x05\xe6CJN5\x83!"
    }
}

_zoeconf = None


class ZoeConfig(ConfigParser):
    def __init__(self):
        super().__init__(interpolation=None)
        self.read_dict(defaults)

    def write_defaults(self, fp):
        tmp = ZoeConfig()
        tmp.write(fp)

    @property
    def history_path(self) -> str:
        return self.get('filesystem', 'history_path')

    @property
    def web_server_name(self) -> str:
        return self.get('apache', 'web_server_name')

    @property
    def proxy_path_url_prefix(self) -> str:
        return self.get('apache', 'proxy_path_prefix')

    @property
    def smtp_server(self) -> str:
        return self.get('smtp', 'server')

    @property
    def smtp_user(self) -> str:
        return self.get('smtp', 'user')

    @property
    def smtp_password(self) -> str:
        return self.get('smtp', 'password')

    @property
    def notebook_warning_age_no_activity(self) -> int:
        return self.getint('intervals', 'notebook_warning_age_no_activity')

    @property
    def notebook_max_age_no_activity(self) -> int:
        return self.getint('intervals', 'notebook_max_age_no_activity')

    @property
    def interval_check_health(self) -> int:
        return self.getint('intervals', 'check_health')

    @property
    def interval_proxy_update_accesses(self) -> int:
        return self.getint('intervals', 'proxy_update_accesses')

    @property
    def apache_log_file(self) -> str:
        return self.get('apache', 'access_log')

    @property
    def apache_proxy_config_file(self) -> str:
        return self.get('apache', 'proxy_config_file')

    @property
    def db_url(self) -> str:
        return self.get('db', 'url')

    @property
    def interval_scheduler_task(self) -> int:
        return self.getint('intervals', 'scheduler_task')

    @property
    def interval_status_refresh(self) -> int:
        return self.getint('intervals', 'status_refresh')

    @property
    def docker_swarm_manager(self) -> str:
        return self.get('docker', 'swarm_manager_url')

    @property
    def cookies_secret_key(self):
        return self.get('flask', 'secret_key')

    @property
    def docker_private_registry(self) -> str:
        return self.get('docker', 'private_registry')


def init(config_file=None) -> ZoeConfig:
    global _zoeconf
    _zoeconf = ZoeConfig()
    if config_file is None:
        _zoeconf.read(config_paths)
    else:
        _zoeconf.read_file(open(config_file))
    return _zoeconf


def zoeconf() -> ZoeConfig:
    return _zoeconf
