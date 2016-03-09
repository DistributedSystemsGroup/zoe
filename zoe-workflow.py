#!/usr/bin/python3

import os
import shutil
import time

from zoe_lib.containers import ZoeContainerAPI
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.info import ZoeInfoAPI
from zoe_lib.predefined_apps import openmpi

WORKSPACE_BASE_PATH = '/mnt/cephfs/zoe-workspaces'

FILES_TO_COPY = [
    ('/home/ubuntu/mpi_test/MPI_Hello', 'MPI_Hello')
]


class ZoeWorkspace:
    def __init__(self, identity, wk_name):
        self._workspace_name = identity['username'] + '-' + wk_name
        self._workspace_path = os.path.join(WORKSPACE_BASE_PATH, self._workspace_name)
        self._workspace_volume = {
            'host_path': self._workspace_path,
            'cont_path': '/mnt/workspace',
            'readonly': False
        }

    def create(self):
        print("Creating workspace {}".format(self._workspace_path))
        os.makedirs(self._workspace_path, exist_ok=False)

    def destroy(self):
        print("Destroying workspace {}".format(self._workspace_path))
        shutil.rmtree(self._workspace_path)

    def get_volume_definition(self):
        return self._workspace_volume

    def put(self, src_filepath, dst_rel_filepath):
        dst_path = os.path.join(self._workspace_path, dst_rel_filepath)
        print("Copying file {} to {}".format(src_filepath, dst_path))
        shutil.copyfile(src_filepath, dst_path)

    def put_string(self, file_contents, dst_rel_filepath):
        dst_path = os.path.join(self._workspace_path, dst_rel_filepath)
        open(dst_path, 'wb').write(file_contents.encode('utf-8'))

    def chmod(self, rel_path: str, octal_perms: int):
        dst_path = os.path.join(self._workspace_path, rel_path)
        os.chmod(dst_path, octal_perms)


class ZoeWorkFlow:
    def __init__(self, identity, name):
        self.identity = identity
        self.name = name
        self.workspace = ZoeWorkspace(identity, name)

        self.exec_api = ZoeExecutionsAPI(self.identity['zoe_url'], self.identity['username'], self.identity['password'])
        self.cont_api = ZoeContainerAPI(self.identity['zoe_url'], self.identity['username'], self.identity['password'])

        info_api = ZoeInfoAPI(self.identity['zoe_url'], self.identity['username'], self.identity['password'])
        zoe_info = info_api.info()
        self.hostname_prefix = zoe_info['name_prefix']

    def generate_hostname(self, process_name: str) -> str:
        return self.hostname_prefix + '-' + process_name + '-' + self.identity['username']

    def start_workflow(self):
        self.workspace.create()

    def end_workflow(self):
        self.workspace.destroy()

    def wait_termination(self, exec_id):
        execution = self.exec_api.execution_get(exec_id)
        while execution['status'] == 'submitted' or execution['status'] == 'running':
            time.sleep(1)
            execution = self.exec_api.execution_get(exec_id)

    def __enter__(self):
        self.start_workflow()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_workflow()


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
    with HelloWorldMPIZoeWorkFlow(identity, 'test') as my_wf:
        # my_wf.copy_from_local('/mnt/ceph/')
        for src, dst in FILES_TO_COPY:
            my_wf.workspace.put(src, dst)
        my_wf.workspace.chmod('MPI_Hello', 0o755)
        app = my_wf.prepare_mpirun()
        print('Starting mpi app')
        exec_id = my_wf.exec_api.execution_start('test', app)
        print('Waiting for termination...')
        my_wf.wait_termination(exec_id)
