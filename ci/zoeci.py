#!/usr/bin/env python3

# Copyright (c) 2016, Quang-Nhat Hoang-Xuan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ZOE CI entry point."""

import sys
from docker import Client

from deploy.frontenddeploy import ZoeFrontendDeploy #pylint: disable=import-error
from deploy.backenddeploy import ZoeBackendDeploy #pylint: disable=import-error

class ZoeDeploy():
    """ Zoe deploy class """
    def __init__(self, dockerUrl, dockerComposePath, image):
        self.current_image = image
        self.type_deploy = 1 if 'prod' in dockerComposePath else 0
        self.backend = ZoeBackendDeploy(dockerUrl, dockerComposePath)
        self.frontend = ZoeFrontendDeploy(dockerUrl, 'apache2')

    def deploy(self):
        """ Deploy frontend and backend """
        try:
            ret_be = self.backend.deploy(self.current_image)
            print('Deployed BE with latest image...')
            if self.type_deploy == 1 and ret_be == 0:
                print('Redeploy BE with previous image')
                self.backend.deploy(self.backend.previousImage)

            ret_fe = 1
            if  self.type_deploy == 1:
                #ret_fe = self.frontend.deploy()
                print('Deployed FE with latest codes...')
                if ret_fe == 0 or ret_be == 0:
                    ret_fe = self.frontend.fallback()
        except Exception as ex:
            print(ex)
            ret_be = 0
        return ret_be and ret_fe

class ZoeImage():
    """ Zoe build/push image class """
    def __init__(self, dockerUrl, tag):
        self.cli = Client(base_url=dockerUrl)
        self.tag = tag

    def build(self):
        """ Build docker image """
        build_ret = 1

        for line in self.cli.build(path='.', tag=self.tag, rm=True):
            print(line)
            if 'error' in str(line):
                build_ret = 0

        return build_ret

    def push(self):
        """ Push docker image """
        push_ret = 1

        for line in self.cli.push(self.tag, stream=True):
            print(line)
            if 'error' in str(line):
                push_ret = 0

        return push_ret

if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit(1)
    else:
        if sys.argv[1] == '0':
            deployer = ZoeDeploy(sys.argv[2], sys.argv[3], sys.argv[4]) # pylint: disable=invalid-name
            ret = deployer.deploy() # pylint: disable=invalid-name
            if ret == 0:
                sys.exit(1)
        elif sys.argv[1] == '1':
            imghandler = ZoeImage(sys.argv[2], sys.argv[3]) # pylint: disable=invalid-name
            ret = imghandler.build() # pylint: disable=invalid-name
            if ret == 0:
                sys.exit(1)
        elif sys.argv[1] == '2':
            imghandler = ZoeImage(sys.argv[2], sys.argv[3]) # pylint: disable=invalid-name
            ret = imghandler.push() # pylint: disable=invalid-name
            if ret == 0:
                sys.exit(1)
