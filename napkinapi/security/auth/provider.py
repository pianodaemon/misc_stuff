from abc import ABCMeta, abstractmethod


class AuthProvider(metaclass=ABCMeta):
    """
    Bla bla
    """

    def __init__(self, app):
        self._app = app


    def __call__(self):
        pass


    @abstractmethod
    def auth_handler(self, username, password):
        pass


    @abstractmethod
    def ident_handler(self, payload):
        pass
