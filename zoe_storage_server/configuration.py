from configparser import ConfigParser

config_paths = [
    'zoe.conf',
    'zoe-storage.conf',
    '/etc/zoe/zoe.conf',
    '/etc/zoe/zoe-storage.conf'
]

defaults = {
    'zoe_storage': {
        'storage_path': "/var/lib/zoe/history",
        'http_listen_address': '127.0.0.1',
        'http_listen_port': 4390,
    }
}

_zoeconf = None


class ZoeStorageConfig(ConfigParser):
    def __init__(self):
        super().__init__(interpolation=None)
        self.read_dict(defaults)

    @staticmethod
    def write_defaults(cls, fp):
        tmp = cls()
        tmp.write(fp)

    @property
    def storage_path(self) -> str:
        return self.get('zoe_storage', 'storage_path')

    @property
    def http_listen_port(self) -> int:
        return self.getint('zoe_storage', 'http_listen_port')

    @property
    def http_listen_address(self) -> str:
        return self.get('zoe_storage', 'http_listen_address')


def conf_init(config_file=None) -> ZoeStorageConfig:
    global _zoeconf
    _zoeconf = ZoeStorageConfig()
    if config_file is None:
        _zoeconf.read(config_paths)
    else:
        _zoeconf.read_file(open(config_file))
    return _zoeconf


def storage_conf() -> ZoeStorageConfig:
    return _zoeconf
