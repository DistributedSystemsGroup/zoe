from configparser import ConfigParser
import os

MAIN_PATH = os.path.split(os.path.abspath(os.path.join(__file__, "..")))[0]


class CAaasConfig:
    def __init__(self, conf_file):
        parser = ConfigParser()
        found = parser.read(conf_file)
        if not found:
            raise ValueError('Configuration file not found')
        self.__dict__.update(parser.items('caaas'))

config = CAaasConfig(os.path.join(MAIN_PATH, 'caaas.ini'))
