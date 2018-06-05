from flask_restful import Resource
from flask_jwt import jwt_required, current_identity
from security.helpers import access_interceptor

class Whoami(Resource):

    decorators = [access_interceptor, jwt_required()]
    def get(self):
        return {'current_login': current_identity.username}
