from bson import json_util
from flask import jsonify, make_response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_restful import reqparse, Resource
from services.UserService import *
from utils.Hash import get_hash


reg_parser = reqparse.RequestParser()
reg_parser.add_argument("email", type=str, default="")
reg_parser.add_argument("password", type=str, default="")


class Users(Resource):
    def get(self):
        return "Use POST method to register", 200

    def post(self):
        args = reg_parser.parse_args()
        found_user = find_user_by_email(args.email)
        if len(args.email) == 0 or len(args.password) == 0:
            return "ERROR! email and password are required fields.", 400
        elif found_user:
            return "Account with this email already exists", 400
        password_hash = get_hash(args.password.encode("utf-8"))
        create_user(args.email, password_hash)
        access_token = create_access_token(identity=args.email)
        return make_response(jsonify(access_token=access_token), 200)
    
    @jwt_required()
    def delete(self):
        args = reg_parser.parse_args()
        if len(args.email) == 0 or len(args.password) == 0:
            return "ERROR! email and password are required fields.", 400
        delete_user(args.email)
        return make_response(
            json_util.dumps({"message": f"User with email {args.email} has been deleted"}),
            200
        )