# Copyright (c) 2015, Daniele Venzano
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

from sqlalchemy import Column, Integer, PickleType, ForeignKey

from zoe_client.state import Base

from common.application_description import ZoeApplication


class ApplicationState(Base):
    """
    :type id: int
    :type user_id: int
    :type description: ZoeApplication
    """
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    description = Column(PickleType())

    def to_dict(self) -> dict:
        ret = {
            'id': self.id,
            'user_id': self.user_id,
            'description': self.description.to_dict(),
        }
        return ret
