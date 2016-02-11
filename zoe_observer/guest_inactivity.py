import logging
import json

from zoe_lib.query import ZoeQueryAPI
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.containers import ZoeContainerAPI
from zoe_observer.config import get_conf

log = logging.getLogger(__name__)

IDLE_TIME = 4 * 60 * 60  # 4h


def check_guests(swarm):
    query_api = ZoeQueryAPI(get_conf().scheduler_url, 'zoeadmin', get_conf().zoeadmin_password)
    exec_api = ZoeExecutionsAPI(get_conf().scheduler_url, 'zoeadmin', get_conf().zoeadmin_password)
    cont_api = ZoeContainerAPI(get_conf().scheduler_url, 'zoeadmin', get_conf().zoeadmin_password)

    guests = query_api.query('user', role='guest')
    execs = exec_api.list()
    for guest in guests:
        my_execs = [e for e in execs if e['owner'] == guest['id']]
        if len(my_execs) > 1:
            log.warning('User {} is a guest and has more than one execution!')
        my_exec = my_execs[0]
        for c in my_exec['containers']:
            c = cont_api.get(c)
            for port in c['ports']:
                if port['name'] == 'Spark application web interface':
                    check_spark_job(swarm, c['docker_id'])


def check_spark_job(swarm, docker_id):
    swarm_exec = swarm.cli.exec_create(docker_id, 'curl http://localhost:4040/api/v1/applications/pyspark-shell/jobs', stderr=False)
    output = swarm.cli.exec_start(swarm_exec['Id'])
    try:
        output = json.loads(output.decode('utf-8'))
    except ValueError:
        return None
    if len(output) == 0:
        return None

    print(output)
