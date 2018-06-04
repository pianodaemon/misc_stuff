from flask import Flask
from flask_restful import Api
from transpec.whoami import Whoami

app = Flask(__name__)
api = Api(app)

from security.fake import FakeAuthProvider

app.config['SECRET_KEY'] = 'super-secret'

auth_provider = FakeAuthProvider(app)

auth_provider()

api.add_resource(Whoami, '/')

if __name__ == '__main__':
    app.run(debug=True)
