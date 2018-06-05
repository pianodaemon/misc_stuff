#!/usr/bin/python3


import logging

from flask import Flask
from flask_restful import Api
from persistence.ds.manager import DsManager
from security.auth.manager import AuthManager
from transpec.resources.whoami import Whoami

app = Flask(__name__)
api = Api(app)

from security.providers.mock import MockAuthProvider

app.config['SECRET_KEY'] = 'super-secret'

uri = "mockdb://XPSrw:j4nusx@mgdb.maxima.uki:27048/admin?authMechanism=SCRAM-SHA-1&replicaSet=XPSdevrep"

logger = logging.getLogger(__name__)
data_source = DsManager.get(logger, uri)

am = AuthManager()
am.subscribe('mock', MockAuthProvider)
auth_provider = am.incept('mock', app=app, ds_adapter=data_source)
auth_provider()

api.add_resource(Whoami, '/')

if __name__ == '__main__':
    app.run(debug=True)
