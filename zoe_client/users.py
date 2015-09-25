from sqlalchemy.orm.exc import NoResultFound

from zoe_client.state import session
from zoe_client.state.user import UserState


def user_check(user_id: int) -> bool:
    state = session()
    num = state.query(UserState).filter_by(id=user_id).count()
    return num == 1


def user_new(email: str) -> UserState:
    state = session()
    user = UserState(email=email)
    state.add(user)
    state.commit()
    return user


def user_get(user_id: int) -> UserState:
    state = session()
    try:
        user = state.query(UserState).filter_by(id=user_id).one()
    except NoResultFound:
        return None
    return user


def user_get_by_email(email: str) -> UserState:
    state = session()
    try:
        user = state.query(UserState).filter_by(email=email).one()
    except NoResultFound:
        return None
    else:
        return user
