from configparser import ConfigParser
from caaas import swarm, app, init_db


def read_config():
    conf = ConfigParser()
    conf.read('caaas.ini')
    return conf


def main():
    conf = read_config()

    init_db(conf['db']['user'], conf['db']['pass'], conf['db']['server'], conf['db']['db'])

    swarm.connect(conf['docker']['swarm-manager'])
    swarm.start_update_thread()

    app.debug = True
    app.run()

if __name__ == "__main__":
    main()
