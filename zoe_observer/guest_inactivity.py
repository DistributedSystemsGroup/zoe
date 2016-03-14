import logging
import json
import datetime

import dateutil.parser

from zoe_lib.query import ZoeQueryAPI
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.containers import ZoeContainerAPI
from zoe_observer.config import get_conf

log = logging.getLogger(__name__)


def check_guests(swarm):
    query_api = ZoeQueryAPI(get_conf().scheduler_url, 'zoeadmin', get_conf().zoeadmin_password)
    exec_api = ZoeExecutionsAPI(get_conf().scheduler_url, 'zoeadmin', get_conf().zoeadmin_password)
    cont_api = ZoeContainerAPI(get_conf().scheduler_url, 'zoeadmin', get_conf().zoeadmin_password)

    guests = query_api.query('user', role='guest')
    execs = exec_api.list()
    for guest in guests:
        my_execs = [e for e in execs if e['owner'] == guest['name']]
        for my_exec in my_execs:
            if len(my_exec['containers']) == 0:
                continue
            my_exec_since_started = datetime.datetime.now() - dateutil.parser.parse(my_exec['time_started'])
            my_exec_since_started = my_exec_since_started.total_seconds()
            terminate = False
            for c in my_exec['containers']:
                c = cont_api.get(c)
                for port in c['ports']:
                    if port['name'] == 'Spark application web interface':
                        idle_time = check_spark_job(swarm, c['docker_id'], my_exec_since_started)
                        if check_if_kill(idle_time):
                            log.info('Execution {} for user {} has been idle for too long, terminating...'.format(my_exec['name'], guest['name']))
                            terminate = True
                            break
                        else:
                            log.debug('Execution {} for user {} has been idle for {} seconds'.format(my_exec['name'], guest['name'], idle_time))
                    if terminate:
                        break
            if terminate:
                exec_api.terminate(my_exec['id'])


def check_if_kill(idle_seconds):
    if idle_seconds > get_conf().spark_activity_timeout:
        return True
    else:
        return False


def check_spark_job(swarm, docker_id, time_started):
    swarm_exec = swarm.cli.exec_create(docker_id, 'curl http://localhost:4040/api/v1/applications/pyspark-shell/jobs', stderr=False)
    output = swarm.cli.exec_start(swarm_exec['Id'])
    try:
        output = json.loads(output.decode('utf-8'))
    except ValueError:
        return time_started
    if len(output) == 0:
        return time_started

    seconds_since_last_job = None
    for job in output:
        if 'submissionTime' not in job:
            continue
        job_time = dateutil.parser.parse(job['submissionTime'])
        job_time_diff = datetime.datetime.now(datetime.timezone.utc) - job_time
        if seconds_since_last_job is None or job_time_diff < seconds_since_last_job:
            seconds_since_last_job = job_time_diff

    if seconds_since_last_job is None:
        return time_started
    else:
        return seconds_since_last_job.total_seconds()
