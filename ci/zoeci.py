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
import docker

from deploy.frontenddeploy import ZoeFrontendDeploy
from deploy.backenddeploy import ZoeBackendDeploy


class ZoeDeploy():
    def __init__(self, dockerUrl, dockerComposePath, image):
        self.currentImage = image
        self.typeDeploy = 1 if 'prod' in dockerComposePath else 0
        self.backend = ZoeBackendDeploy(dockerUrl, dockerComposePath)
        self.frontend = ZoeFrontendDeploy(dockerUrl, 'apache2')

    def deploy(self):
        try:
            retBE = self.backend.deploy(self.currentImage)
            print('Deployed BE with latest image...')
            if self.typeDeploy == 1 and retBE == 0:
                print('Redeploy BE with previous image')
                self.backend.deploy(self.backend.previousImage)

            retFE = 1
            if self.typeDeploy == 1:
                #retFE = self.frontend.deploy()
                print('Deployed FE with latest codes...')
                if retFE == 0 or retBE == 0:
                    retFE = self.frontend.fallback()
        except Exception as ex:
            print(ex)
            retBE = 0
        return retBE and retFE

class ZoeImage():
    def __init__(self, dockerUrl, tag):
        self.cli = docker.DockerClient(base_url=dockerUrl)
        self.tag = tag

    def build(self):
        """ Build docker image """
        ret = 1
        try:
            self.cli.images.build(path='.', tag=self.tag, rm=True)
        except Exception:
            ret = 0
            pass
        return ret

    def push(self):
        """ Push docker image """
        ret = 1
        try:
            self.cli.images.push(self.tag, stream=True)
        except Exception:
            ret = 0
            pass
        return ret

if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit(1)
    else:
        if sys.argv[1] == '0':
            deployer = ZoeDeploy(sys.argv[2], sys.argv[3], sys.argv[4])
            ret = deployer.deploy()
            if ret == 0:
                sys.exit(1)
        elif sys.argv[1] == '1':
            imghandler = ZoeImage(sys.argv[2], sys.argv[3])
            ret = imghandler.build()
            if ret == 0:
                sys.exit(1)
        elif sys.argv[1] == '2':
            imghandler = ZoeImage(sys.argv[2], sys.argv[3])
            ret = imghandler.push()
            if ret == 0:
                sys.exit(1)
