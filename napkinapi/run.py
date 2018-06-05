from flask import Flask
from flask_restful import Api
from transpec.resources.whoami import Whoami

app = Flask(__name__)
api = Api(app)

from security.providers.mock import MockAuthProvider

app.config['SECRET_KEY'] = 'super-secret'

auth_provider = MockAuthProvider(app)

auth_provider()

api.add_resource(Whoami, '/')

if __name__ == '__main__':
    app.run(debug=True)
