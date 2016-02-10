# Copyright (c) 2016, Daniele Venzano
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


class BaseBlobs:
    def init(self):
        pass

    def store_blob(self, kind, name, data):
        raise NotImplementedError

    def load_blob(self, kind, name):
        raise NotImplementedError

    def delete_blob(self, kind, name):
        raise NotImplementedError

    def list_blobs(self, kind):
        raise NotImplementedError
