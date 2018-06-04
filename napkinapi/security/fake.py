from abc import ABCMeta, abstractmethod
from flask_jwt import JWT
from persistence.models.users import User
from werkzeug.security import safe_str_cmp


class AuthProvider(metaclass=ABCMeta):
    """
    Bla bla
    """

    def __init__(self, app):
        self._app = app


    def __call__(self):
         self._jwt = JWT(self._app, self.auth_handler, self.ident_handler)       


    @abstractmethod
    def auth_handler(self, username, password):
        pass


    @abstractmethod
    def ident_handler(self, payload):
        pass



class FakeAuthProvider(AuthProvider):
    """
    Bla bla implements whatever
    """

    __USERS = [
        User(1, 'user1', 'abcxyz'),
        User(2, 'user2', 'abcxyz'),
    ]

    __USERNAME_TABLE = {u.username: u for u in __USERS}
    __USERID_TABLE = {u.id: u for u in __USERS}


    def __init__(self, app, *args, **kwargs):
        super().__init__(app)


    def __call__(self):
        super().__call__()


    def auth_handler(self, username, password):
        """"""
        u = self.__USERNAME_TABLE.get(username, None)
        if u and safe_str_cmp(u.password.encode('utf-8'), password.encode('utf-8')):
            return u


    def ident_handler(self, payload):
        """"""
        user_id = payload['identity']
        return self.__USERID_TABLE.get(user_id, None)
