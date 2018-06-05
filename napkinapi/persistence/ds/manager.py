from urllib.parse import urlparse
from persistence.adapters.mongodb import MongoAdapter
from persistence.adapters.mock import MockAdapter


class DsManager(object):

    __SUPPORTED = { 'mongodb': MongoAdapter, 'mockdb': MockAdapter }

    @staticmethod
    def get(logger, uri):

        def resolve(n):
            ic = DsManager.__SUPPORTED.get(n.scheme.lower(), None)
            if ic is not None:
                return ic(logger, uri)
            else:
                raise Exception("Such uri is not supported yet")

        uri_parsed = urlparse(uri)
        return resolve(uri_parsed)
