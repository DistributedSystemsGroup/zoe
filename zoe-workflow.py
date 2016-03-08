#!/usr/bin/python3

import os
import shutil

from zoe_lib.containers import ZoeContainerAPI
from zoe_lib.exceptions import ZoeAPIException
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.predefined_apps import copier

WORKSPACE_BASE_PATH = '/mnt/nfs/zoe-workspaces'


class ZoeWorkFlow:
    def __init__(self, identity, name):
        self.identity = identity
        self.name = name
        self._workspace_name = identity['username'] + '-' + name
        self._workspace_path = os.path.join(WORKSPACE_BASE_PATH, self._workspace_name)
        self._workspace_volume = {
            'type': 'volume',
            'host_path': self._workspace_path,
            'cont_path': '/workspace'
        }

    def start_workflow(self):
        os.makedirs(self._workspace_path, exist_ok=False)

    def end_workflow(self):
        shutil.rmtree(self._workspace_path)

    def __enter__(self):
        self.start_workflow()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_workflow()


class HelloWorldMPIZoeWorkFlow(ZoeWorkFlow):
    def copy_from_local(self, source_path):

        copier_app = copier.copier_app()

if __name__ == "__main__":
    identity = {
        'username': os.getenv('ZOE_USER'),
        'password': os.getenv('ZOE_PASS'),
        'zoe_url': os.getenv('ZOE_URL')
    }
    with HelloWorldMPIZoeWorkFlow(identity, 'test') as my_wf:

