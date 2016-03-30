#!/usr/bin/python3

import os

from zoe_lib.predefined_apps import openmpi
from zoe_lib.workflow import ZoeWorkFlow

WORKSPACE_BASE_PATH = '/mnt/cephfs/zoe-workspaces'


def prepare_mpirun(wf):
    count = 4
    mpihosts = ''
    for i in range(count):
        mpihosts += wf.generate_hostname('openmpi-worker-{}'.format(i)) + '\n'
    mpihosts += '\n'
    wf.workspace.put_string(mpihosts, 'mpihosts')
    cmdline = 'mpirun -np {} --hostfile mpihosts ./MPI_Hello'.format(count)
    zoe_app = openmpi.openmpi_app(name='mpi-hello-world', mpirun_commandline=cmdline, worker_count=count)
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
