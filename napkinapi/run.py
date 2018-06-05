#!/usr/bin/python3


import logging

from flask import Flask
from flask_restful import Api
from persistence.ds.manager import DsManager
from security.auth.manager import AuthManager
from transpec.resources.whoami import Whoami
from persistence.adapters.mongodb import MongoAdapter
from persistence.adapters.mock import MockAdapter
from security.providers.mock import MockAuthProvider


app = Flask(__name__)
api = Api(app)

app.config['SECRET_KEY'] = 'super-secret'

uri = "mockdb://XPSrw:j4nusx@mgdb.maxima.uki:27048/admin?authMechanism=SCRAM-SHA-1&replicaSet=XPSdevrep"

dm = DsManager()
dm.subscribe('mongodb', MongoAdapter)
dm.subscribe('mockdb', MockAdapter)
data_source = dm.incept('mockdb', uri=uri)

am = AuthManager()
am.subscribe('mockdb', MockAuthProvider)
auth_provider = am.incept('mockdb', app=app, ds_adapter=data_source)
auth_provider()

api.add_resource(Whoami, '/')

if __name__ == '__main__':
    app.run(debug=True)
