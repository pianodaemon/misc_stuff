import logging
from persistence.ds.adapter import Adapter, AdapterException


class MockAdapter(Adapter):
    """
    Mock database adapter class
    """

    _client = None

    def __init__(self, uri):
        super().__init__(logging.getLogger(__name__))
        self._uri = uri


    def open(self):

        def connect():
            try:
                return self.FakeClient(self.logger, self._uri)
            except:
                raise AdapterException(
                    "An error occuried when connecting mock")

        self._client = connect()
        self.logger.debug("Connected to mock")


    def release(self):

        if not self._client:
            raise AdapterException("Never connected to mock")

        self._client.close()
        self._client = None
        self.logger.debug("Disconnected from mock")

    class FakeClient:

        def __init__(self, l, fc_uri):
            self.__l = l
            self.__l.debug("Performing fake connection to {}".format(
                fc_uri))

        def close(self):
            self.__l.debug("Performing fake disconnection from mock")
