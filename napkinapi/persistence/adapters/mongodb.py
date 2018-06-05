import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from persistence.ds.adapter import Adapter, AdapterException


class MongoAdapter(Adapter):
    """
    Mongo database adapter class
    """

    _client = None

    def __init__(self, uri):
        super().__init__(logging.getLogger(__name__))
        self._uri = uri


    def open(self):

        def connect():
            try:
                return MongoClient(self._uri)
            except ConnectionFailure as e:
                raise DbAdapterException(
                    "An error occuried when connecting mongo: {}".format(e))

        self._client = connect()
        self.logger.info("Connected to mongo")


    def release(self):

        if not self._client:
            raise DbAdapterException("Never connected to mongo")

        self._client.close()
        self._client = None
        self.logger.info("Disconnected from mongo")
