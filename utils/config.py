from configparser import ConfigParser
import os

MAIN_PATH = os.path.split(os.path.abspath(os.path.join(__file__, "..")))[0]

conf = ConfigParser()
conf.read(os.path.join(MAIN_PATH, 'caaas.ini'))


def get_swarm_manager_address():
    return conf['docker']['swarm-manager']


def get_database_config():
    db_config = {
        'user': conf['db']['user'],
        'password': conf['db']['pass'],
        'host': conf['db']['server'],
        'database': conf['db']['db'],
        'buffered': True
    }
    return db_config


def get_proxy_base():
    return conf["proxy"]["base_url"]


def volume_path():
    return conf["docker"]['volume-path']


def get_app_history_path():
    return conf["caaas"]["history_path"]


def get_app_history_count():
    return int(conf["caaas"]["history_per_user_count"])


def get_smtp_info() -> dict:
    ret = {
        'user': conf["smtp"]["user"],
        'pass': conf["smtp"]["pass"],
        'server': conf["smtp"]["server"],
    }
    return ret


def get_cleanup_interval() -> int:
    return int(conf["caaas"]["cleanup_thread_interval"])


def get_flask_server_url() -> str:
    return conf["caaas"]["base_flask_url"]
