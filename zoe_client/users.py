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

"""
This module contains all user-related API calls that a Zoe client can use.

For now Zoe implements a bare minimum of user management. Users are distinguished by their email address
and there are no passwords. Authentication is a well-known problem with lots of solutions, eventually
we will implement one.
"""

from sqlalchemy.orm.exc import NoResultFound

from zoe_client.state import session
from zoe_client.state.user import UserState


def user_check(user_id: int) -> bool:
    """
    Checks if a given user_id exists.

    :param user_id: the user_id to check
    :return: True if the user_id exists, False otherwise
    """
    with session() as state:
        num = state.query(UserState).filter_by(id=user_id).count()
        return num == 1


def user_new(email: str) -> UserState:
    """
    Creates a new user, given his email address.

    :param email: the user email address
    :return: the user object from SQLAlchemy
    """
    with session() as state:
        user = UserState(email=email)
        state.add(user)
        state.commit()
        return user


def user_get(user_id: int) -> UserState:
    """
    Get an user object given a user_id.

    :param user_id: the user_id to look for
    :return: the user object from SQLAlchemy, or None
    """
    with session() as state:
        try:
            user = state.query(UserState).filter_by(id=user_id).one()
        except NoResultFound:
            return None
        return user


def user_get_by_email(email: str) -> UserState:
    """
    Return the first user with the matching email address. Duplicate email addresses should never exist, but the rule is not enforced in the database.

    :param email: the user's email address
    :return: the user object from SQLAlchemy, or None
    """
    with session() as state:
        try:
            user = state.query(UserState).filter_by(email=email).one()
        except NoResultFound:
            return None
        else:
            return user
