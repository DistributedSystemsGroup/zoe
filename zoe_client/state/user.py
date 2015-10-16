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

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from zoe_client.state import Base


class UserState(Base):
    """
    :type id: int
    :type email: str
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(128))

    applications = relationship("ApplicationState", backref="user")

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email
        }
