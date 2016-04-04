#!/usr/bin/python3

import os
import json

from zoe_lib.workflow import ZoeWorkFlow

WORKSPACE_BASE_PATH = '/mnt/cephfs/zoe-workspaces'


ZOE_WORKER_JSON = '''
        {
            "command": "",
            "docker_image": "192.168.45.252:5000/zoerepo/openmpi-worker",
            "environment": [],
            "monitor": false,
            "name": "mpiworker",
            "ports": [],
            "required_resources": {
                "memory": 1073741824
            },
            "volumes": []
        }
'''

ZOE_MPIRUN_JSON = '''
        {
            "command": "mpirun <options>",
            "docker_image": "192.168.45.252:5000/zoerepo/openmpi-worker",
            "environment": [],
            "monitor": true,
            "name": "mpirun",
            "ports": [],
            "required_resources": {
                "memory": 1073741824
            },
            "volumes": []
        }
'''

ZOE_APP_BASE_JSON = '''
{
    "name": "openmpi-hello",
    "priority": 512,
    "requires_binary": true,
    "services": [],
    "version": 1,
    "will_end": true
}
'''


def prepare_mpirun(wf):
    count = 4
    mpihosts = ''
    for i in range(count):
        mpihosts += wf.generate_hostname('openmpi-worker-{}'.format(i)) + '\n'
    mpihosts += '\n'
    wf.workspace.put_string(mpihosts, 'mpihosts')
    cmdline = 'mpirun -np {} --hostfile mpihosts ./MPI_Hello'.format(count)
    zoe_app = json.loads(ZOE_APP_BASE_JSON)
    zoe_app['name'] = 'mpi-hello-world'
    mpirun_service = json.loads(ZOE_MPIRUN_JSON)
    mpirun_service['command'] = cmdline
    for wc in range(count):
        mpiworker = json.loads(ZOE_WORKER_JSON)
        mpiworker['name'] = 'mpiworker{}'.format(wc)
        zoe_app['services'].append(mpiworker)
    zoe_app['services'].append(mpirun_service)
    return zoe_app


if __name__ == "__main__":
    identity = {
        'username': os.getenv('ZOE_USER'),
        'password': os.getenv('ZOE_PASS'),
        'zoe_url': os.getenv('ZOE_URL')
    }
    with ZoeWorkFlow(WORKSPACE_BASE_PATH, identity, 'mpi-test') as my_wf:
        my_wf.workspace.put('/home/ubuntu/mpi_test/MPI_Hello', 'MPI_Hello')
        my_wf.workspace.chmod('MPI_Hello', 0o755)
        app = prepare_mpirun(my_wf)
        print('Starting mpi app')
        exec_id = my_wf.execution_start(app)
        print('Waiting for termination...')
        my_wf.wait_termination(exec_id)
