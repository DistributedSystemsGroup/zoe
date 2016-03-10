#!/usr/bin/python3

import os

from zoe_lib.predefined_apps import openmpi
from zoe_lib.workflow import ZoeWorkFlow

WORKSPACE_BASE_PATH = '/mnt/cephfs/zoe-workspaces'

FILES_TO_COPY = [
    ('/home/ubuntu/mpi_test/MPI_Hello', 'MPI_Hello')
]


class HelloWorldMPIZoeWorkFlow(ZoeWorkFlow):
    # def copy_from_local(self, source_path):
    #     if source_path[-1] == '/':
    #         source_path = source_path[:-1]
    #     host_path, source = os.path.split(source_path)
    #     src_volume = {
    #         'host_path': host_path,
    #         'cont_path': '/mnt/source',
    #         'readonly': True
    #     }
    #     copier_app = copier.copier_app(src_volume, source, self._workspace_volume, source)
    #     exec_id = self.exec_api.execution_start('copy', copier_app)
    #     self._wait_termination(exec_id)

    def prepare_mpirun(self):
        count = 4
        mpihosts = ''
        for i in range(count):
            mpihosts += self.generate_hostname('openmpi-worker-{}'.format(i)) + '\n'
        mpihosts += '\n'
        self.workspace.put_string(mpihosts, 'mpihosts')
        cmdline = 'mpirun -np {} --hostfile mpihosts ./MPI_Hello'.format(count)
        zoe_app = openmpi.openmpi_app(name='mpi-hello-world', workspace_volume=self.workspace.get_volume_definition(), mpirun_commandline=cmdline, worker_count=count)
        return zoe_app

if __name__ == "__main__":
    identity = {
        'username': os.getenv('ZOE_USER'),
        'password': os.getenv('ZOE_PASS'),
        'zoe_url': os.getenv('ZOE_URL')
    }
    with HelloWorldMPIZoeWorkFlow(WORKSPACE_BASE_PATH, identity, 'test') as my_wf:
        # my_wf.copy_from_local('/mnt/ceph/')
        for src, dst in FILES_TO_COPY:
            my_wf.workspace.put(src, dst)
        my_wf.workspace.chmod('MPI_Hello', 0o755)
        app = my_wf.prepare_mpirun()
        print('Starting mpi app')
        exec_id = my_wf.exec_api.execution_start('test', app)
        print('Waiting for termination...')
        my_wf.wait_termination(exec_id)
