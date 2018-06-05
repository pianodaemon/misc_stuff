from abc import ABCMeta, abstractmethod
from flask_jwt import JWT


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
