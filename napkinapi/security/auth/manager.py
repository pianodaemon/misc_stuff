from misc.factory import TrivialFactory


class AuthManager(TrivialFactory):
    """
    Bla bla
    """

    def __init__(self, app):
        super().__init__()
        self._app = app

    def incept(self, i, ds_a):
        return super().incept(i, app=self._app, ds_adapter=ds_a)
