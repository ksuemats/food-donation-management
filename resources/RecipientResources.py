from bson import json_util
from flask import abort, make_response, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import reqparse, Resource
from models.Recipient import *
from services.RecipientServices import *


headers = {"Content-Type": "application/json"}

post_parser = reqparse.RequestParser()
post_parser.add_argument("first_name", type=str, required=False, help="First name")
post_parser.add_argument("last_name", type=str, required=False, help="Last name")
post_parser.add_argument(
    "organization_name", type=str, required=False, help="Organization name"
)
post_parser.add_argument("email", type=str, required=True, help="Email is required")
post_parser.add_argument(
    "phone_number", type=str, required=True, help="Phone number is required"
)
post_parser.add_argument(
    "street_and_number", type=str, required=True, help="Street and number are required"
)
post_parser.add_argument("city", type=str, required=True, help="City is required")
post_parser.add_argument("state", type=str, required=True, help="State is required")
post_parser.add_argument(
    "zip_code", type=str, required=True, help="ZIP code is required"
)
post_parser.add_argument("country", type=str, required=True, help="Country is required")
post_parser.add_argument("ein", type=str, required=True, help="EIN is required")

patch_parser = reqparse.RequestParser()
patch_parser.add_argument("phone_number", type=str, required=False)
patch_parser.add_argument("street_and_number", type=str, required=False)
patch_parser.add_argument("city", type=str, required=False)
patch_parser.add_argument("state", type=str, required=False)
patch_parser.add_argument("zip_code", type=str, required=False)
patch_parser.add_argument("country", type=str, required=False)
patch_parser.add_argument("compliance_status", type=str, required=False)
patch_parser.add_argument("tax_status", type=str, required=False)


class RecipientResource(Resource):
    def get(self, recipient_id=None):
        if recipient_id:
            recipient_data = get_recipient(recipient_id)
            if not recipient_data:
                return make_response(
                    json_util.dumps(
                        {"error": f"Recipient with ID {recipient_id} not found"}
                    ),
                    404,
                    headers,
                )
            return make_response(json_util.dumps(recipient_data), 200, headers)
        else:
            args = request.args
            recipients = get_all_recipients(
                page=int(args.get("page", 1)),
                pagesize=int(args.get("pagesize", 10)),
                recipient_id=args.get("id"),
                name=args.get("name"),
                tax_status=args.get("501c3"),
                compliance_status=args.get("goodstanding"),
                sort_by=args.get("numberdonations"),
            )
            return make_response(json_util.dumps(recipients), 200, headers)

    @jwt_required()
    def post(self):
        email_identity = get_jwt_identity()
        recipient = get_recipient_by_email(email_identity)
        if not recipient or email_identity != recipient.email:
            return abort(403)
        data = request.get_json()
        address = {
            "street_and_number": data.get("street_and_number"),
            "city": data.get("city"),
            "state": data.get("state"),
            "zip_code": data.get("zip_code"),
            "country": data.get("country"),
        }
        recipient = create_recipient(
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            organization_name=data.get("organization_name"),
            email=data["email"],
            phone_number=data["phone_number"],
            address=address,
            ein=data["ein"],
        )
        return make_response(
            json_util.dumps(recipient.to_mongo().to_dict()), 201, headers
        )

    @jwt_required()
    def patch(self, recipient_id):
        email_identity = get_jwt_identity()
        recipient = get_recipient_by_email(email_identity)
        if not recipient or email_identity != recipient.email:
            return abort(403)
        data = request.get_json()
        updated_recipient = update_recipient(
            recipient_id=recipient_id,
            phone_number=data.get("phone_number"),
            address=data.get("address"),
            tax_status=data.get("tax_status"),
            compliance_status=data.get("compliance_status"),
        )
        if not updated_recipient:
            return make_response(
                {"error": f"Recipient with ID {recipient_id} not found"}, 404, headers
            )
        return make_response(json_util.dumps(updated_recipient), 200, headers)

    @jwt_required()
    def delete(self, recipient_id):
        email_identity = get_jwt_identity()
        recipient = get_recipient_by_email(email_identity)
        if not recipient or email_identity != recipient.email:
            return abort(403)
        if not recipient:
            return make_response(
                json_util.dumps(
                    {"error": f"Recipient with ID {recipient_id} not found"}
                ),
                404,
                headers,
            )
        delete_recipient(recipient_id)
        return make_response(
            json_util.dumps(
                {"message": f"Recipient with ID {recipient_id} has been deleted"}
            ),
            200,
            headers,
        )


class DonationLogResource(Resource):
    def get(self, recipient_id):
        logs = get_recipient_donation_logs(recipient_id)
        if logs is None:
            return make_response(
                json_util.dumps(
                    {"error": f"Recipient with ID {recipient_id} not found"}
                ),
                404,
                headers,
            )
        return make_response(json_util.dumps(logs), 200)

    @jwt_required()
    def post(self, recipient_id):
        email_identity = get_jwt_identity()
        recipient = get_recipient_by_email(email_identity)
        if not recipient or email_identity != recipient.email:
            return abort(403)
        data = request.get_json()
        log = add_recipient_donation_log(recipient_id=recipient_id, donation_data=data)
        if not log:
            return make_response(
                json_util.dumps(
                    {"error": f"Recipient with ID {recipient_id} not found"}
                ),
                404,
                headers,
            )
        return make_response(json_util.dumps(log), 201, headers)


class TaxStatusResource(Resource):
    def get(self, recipient_id):
        status = get_recipient_tax_status(recipient_id)
        if not status:
            return make_response(
                json_util.dumps({"error": "Tax status not found"}), 404, headers
            )
        return make_response(json_util.dumps(status), 200)

    @jwt_required()
    def patch(self, recipient_id):
        email_identity = get_jwt_identity()
        recipient = get_recipient_by_email(email_identity)
        if not recipient or email_identity != recipient.email:
            return abort(403)
        try:
            data = request.get_json()
            if not data or "status" not in data:
                return make_response(
                    {"error": "Missing required field 'status' in request body"}, 400
                )
            tax_status = update_recipient_tax_status(
                recipient_id=recipient_id,
                status=data["status"],
                verification_date=datetime.datetime.now(),
            )
            if not tax_status:
                return make_response(
                    json_util.dumps(
                        {"error": f"Recipient with ID {recipient_id} not found"}
                    ),
                    404,
                    headers,
                )
            return make_response(json_util.dumps(tax_status), 200)
        except Exception as ex:
            print(
                f"Error while updating tax exempt status for recipient {recipient_id}: {ex}"
            )
            return make_response(
                {"error": "An error occurred while updating tax exempt status"}, 500
            )


class ComplianceStatusResource(Resource):
    def get(self, recipient_id):
        compliance = get_recipient_compliance_status(recipient_id)
        if not compliance:
            return make_response(
                json_util.dumps({"error": "Compliance status not found"}), 404, headers
            )
        return make_response(json_util.dumps(compliance), 200)

    @jwt_required()
    def patch(self, recipient_id):
        email_identity = get_jwt_identity()
        recipient = get_recipient_by_email(email_identity)
        if not recipient or email_identity != recipient.email:
            return abort(403)
        try:
            data = request.get_json()
            if not data or "status" not in data:
                return make_response(
                    {"error": "Missing required field 'status' in request body"}, 400
                )
            compliance_status = update_recipient_compliance_status(
                recipient_id=recipient_id,
                status=data["status"],
                verification_date=datetime.datetime.now(),
            )
            if not compliance_status:
                return make_response(
                    json_util.dumps(
                        {"error": f"Recipient with ID {recipient_id} not found"}
                    ),
                    404,
                    headers,
                )
            return make_response(json_util.dumps(compliance_status), 200)
        except Exception as ex:
            print(
                f"Error while updating compliance status for recipient {recipient_id}: {ex}"
            )
            return make_response(
                {"error": "An error occurred while updating compliance status"}, 500
            )
