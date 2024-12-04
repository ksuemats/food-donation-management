from database.db import initialize_db
from datetime import timedelta
from flask import Flask, abort, jsonify, make_response
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt
from flask_restful import Api, reqparse, Resource
from resources.DonationResources import (
    DonationListingResource,
    DonationFormResource,
    DonationReceiptResource,
    ReceiptResource,
    ReceiptDetailResource,
    DonationDetailResource,
)
from resources.DonorResources import DonorResource, RatingsResource, ImpactLogResource
from resources.RecipientResources import (
    RecipientResource,
    DonationLogResource,
    TaxStatusResource,
    ComplianceStatusResource,
)
from resources.UserResources import Users
from services.UserService import *
from utils.JSONEncoder import MongoEngineJSONEncoder

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {
    "db": "app-donation",
    "host": "mongodb://localhost:27017/app-donation",
}
app.config['JWT_SECRET_KEY'] = "random-key"
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access", "refresh"]
jwt = JWTManager(app)
initialize_db(app)
app.json_encoder = MongoEngineJSONEncoder
api = Api(app)
blacklist = set()

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in blacklist


login_parser = reqparse.RequestParser()
login_parser.add_argument("email", type=str, default="")
login_parser.add_argument("password", type=str, default="")


class Sessions(Resource):
    def post(self):
        args = login_parser.parse_args()
        if len(args.email) == 0 or len(args.password) == 0:
            abort(400, "email and password are required fields")
        found_user = find_user_by_email(args.email)
        if found_user:
            password_hash = get_hash(args.password.encode("utf-8"))
            if password_hash == found_user.password_hash:
                access_token = create_access_token(
                    identity=args.email, expires_delta=timedelta(seconds=900)
                )
                return make_response(jsonify(access_token=access_token), 200)
        abort(401, "Invalid credentials")
    
    @jwt_required()
    def delete(self):
        jti = get_jwt()["jti"]
        blacklist.add(jti)
        return {"message": "Successfully logged out"}, 200


# User endpoints
api.add_resource(Users, '/users')

# Session endpoints
api.add_resource(Sessions, "/sessions")


# Donation endpoints
api.add_resource(
    DonationListingResource,
    "/donations/listings",
    "/donations/listings/<string:listing_id>",
)
api.add_resource(
    DonationFormResource,
    "/donations/listings/<string:listing_id>/forms",
    "/donations/listings/<string:listing_id>/forms/<string:form_id>",
)
api.add_resource(
    DonationReceiptResource, "/donations/listings/<string:listing_id>/receipts"
)
api.add_resource(ReceiptResource, "/donations/receipts")
api.add_resource(ReceiptDetailResource, "/donations/receipts/<string:receipt_id>")
api.add_resource(DonationDetailResource, "/donations/<string:donation_id>")

# Donor endpoints
api.add_resource(DonorResource, "/donors", "/donors/<string:donor_id>")
api.add_resource(
    RatingsResource,
    "/donors/<string:donor_id>/ratings",
    "/donors/<string:donor_id>/ratings/<string:donation_id>",
)
api.add_resource(
    ImpactLogResource,
    "/donors/<string:donor_id>/impactlog",
    "/donors/<string:donor_id>/impactlog/<string:donation_id>",
)

# Recipient endpoints
api.add_resource(RecipientResource, "/recipients", "/recipients/<string:recipient_id>")
api.add_resource(DonationLogResource, "/recipients/<string:recipient_id>/donationlog")
api.add_resource(TaxStatusResource, "/recipients/<string:recipient_id>/taxexempt")
api.add_resource(
    ComplianceStatusResource, "/recipients/<string:recipient_id>/compliance"
)


if __name__ == "__main__":
    app.run()
