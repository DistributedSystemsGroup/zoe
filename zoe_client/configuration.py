from configparser import ConfigParser

config_paths = [
    'zoe.conf',
    'zoe-client.conf',
    '/etc/zoe/zoe.conf',
    '/etc/zoe/zoe-client.conf'
]

defaults = {
    'zoe_client': {
        'db_connect': 'mysql+mysqlconnector://zoe:pass@dbhost/zoe',
        'scheduler_ipc_address': 'localhost',
        'scheduler_ipc_port': 8723
    },
    'zoe_web': {
        'smtp_server': 'smtp.exmaple.com',
        'smtp_user': 'zoe@exmaple.com',
        'smtp_password': 'changeme',
        'cookie_secret': b"\xc3\xb0\xa7\xff\x8fH'\xf7m\x1c\xa2\x92F\x1d\xdcz\x05\xe6CJN5\x83!",
        'web_server_name': 'localhost'
    }
}

_zoeconf = None


class ZoeClientConfig(ConfigParser):
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


def conf_init(config_file=None) -> ZoeClientConfig:
    global _zoeconf
    _zoeconf = ZoeClientConfig()
    if config_file is None:
        _zoeconf.read(config_paths)
    else:
        _zoeconf.read_file(open(config_file))
    return _zoeconf


def client_conf() -> ZoeClientConfig:
    return _zoeconf
