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
