from flask_jwt import current_identity
from flask_restful import abort
from functools import wraps


def access_interceptor(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_identity.username == 'user1':
            return func(*args, **kwargs)
        return abort(401)
    return wrapper
