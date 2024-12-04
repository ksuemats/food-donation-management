from bson import json_util
from flask import abort, make_response, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import reqparse, Resource
from models.Donor import *
from services.DonorServices import *
from services.RecipientServices import *


headers = {"Content-Type": "application/json"}

post_parser = reqparse.RequestParser()
post_parser.add_argument(
    "first_name", type=str, required=True, help="First name is required"
)
post_parser.add_argument(
    "last_name", type=str, required=True, help="Last name is required"
)
post_parser.add_argument("email", type=str, required=True, help="Email is required")
post_parser.add_argument("phone_number", type=str, required=False, help="Phone number")
post_parser.add_argument(
    "street_and_number", type=str, required=True, help="Street and number are required"
)
post_parser.add_argument("city", type=str, required=True, help="City is required")
post_parser.add_argument("state", type=str, required=True, help="State is required")
post_parser.add_argument(
    "zip_code", type=str, required=True, help="ZIP code is required"
)
post_parser.add_argument("country", type=str, required=True, help="Country is required")
post_parser.add_argument("tax_id", type=str, required=True, help="Tax ID is required")
post_parser.add_argument(
    "company_association",
    type=str,
    required=True,
    help="Company association is required",
)

patch_parser = reqparse.RequestParser()
patch_parser.add_argument("phone_number", type=str, required=False)
patch_parser.add_argument("street_and_number", type=str, required=False)
patch_parser.add_argument("city", type=str, required=False)
patch_parser.add_argument("state", type=str, required=False)
patch_parser.add_argument("zip_code", type=str, required=False)
patch_parser.add_argument("country", type=str, required=False)
patch_parser.add_argument("company_association", type=str, required=False)


class DonorResource(Resource):
    def get(self, donor_id=None):
        if donor_id:
            donor_data = get_donor(donor_id)
            if not donor_data:
                return make_response(
                    json_util.dumps({"error": f"Donor with ID {donor_id} not found"}),
                    404,
                    headers,
                )
            return make_response(json_util.dumps(donor_data), 200, headers)
        else:
            args = request.args
            donors = get_all_donors(
                page=int(args.get("page", 1)),
                pagesize=int(args.get("pagesize", 10)),
                donor_id=args.get("id"),
                name=args.get("name"),
                email=args.get("email"),
                sort_by=args.get("numberdonations"),
            )
            return make_response(json_util.dumps(donors), 200, headers)

    @jwt_required()
    def post(self):
        email_identity = get_jwt_identity()
        donor = get_donor_by_email(email_identity)
        if donor and email_identity != donor.email:
            return abort(403)
        data = request.get_json()
        address = {
            "street_and_number": data.get("street_and_number"),
            "city": data.get("city"),
            "state": data.get("state"),
            "zip_code": data.get("zip_code"),
            "country": data.get("country"),
        }
        donor = create_donor(
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            email=data.get("email"),
            phone_number=data.get("phone_number"),
            address=address,
            tax_id=data.get("tax_id"),
            company_association=data.get("company_association"),
        )
        return make_response(json_util.dumps(donor.to_mongo().to_dict()), 201, headers)

    @jwt_required()
    def patch(self, donor_id):
        email_identity = get_jwt_identity()
        donor = get_donor_by_email(email_identity)
        if donor and email_identity != donor.email:
            return abort(403)
        data = request.get_json()
        updated_donor = update_donor(
            donor_id=donor_id,
            phone_number=data.get("phone_number"),
            address=data.get("address"),
            company_association=data.get("company_association"),
        )
        if not updated_donor:
            return make_response(
                {"error": f"Donor with ID {donor_id} not found"}, 404, headers
            )
        return make_response(json_util.dumps(updated_donor), 200, headers)

    @jwt_required()
    def delete(self, donor_id):
        email_identity = get_jwt_identity()
        donor = get_donor_by_email(email_identity)
        if donor and email_identity != donor.email:
            return abort(403)
        if not donor:
            return make_response(
                json_util.dumps({"error": f"Donor with ID {donor_id} not found"}),
                404,
                headers,
            )
        delete_donor(donor_id)
        return make_response(
            json_util.dumps({"message": f"Donor with ID {donor_id} has been deleted"}),
            200,
            headers,
        )


class RatingsResource(Resource):
    def get(self, donor_id):
        ratings = get_ratings(donor_id)
        if not ratings:
            return {"message": f"Donor with ID {donor_id} not found"}, 404
        return make_response(json_util.dumps(ratings), 200)

    @jwt_required()
    def post(self, donor_id):
        email_identity = get_jwt_identity()
        recipient = get_recipient_by_email(email_identity)
        if not recipient or email_identity != recipient.email:
            return abort(403)
        data = request.get_json()
        if "donation_id" not in data or "stars" not in data:
            return {"message": "Missing required fields: donation_id, stars"}, 400

        result = create_rating(
            donor_id=donor_id,
            donation_id=data["donation_id"],
            stars=data["stars"],
            message=data.get("message"),
        )
        if "error" in result:
            return {"message": result["error"]}, 404
        return make_response(json_util.dumps(result), 201)

    @jwt_required()
    def patch(self, donor_id, donation_id):
        email_identity = get_jwt_identity()
        recipient = get_recipient_by_email(email_identity)
        if not recipient or email_identity != recipient.email:
            return abort(403)
        data = request.get_json()
        if not data:
            return {"message": "No update data provided"}, 400

        result = update_rating(
            donor_id=donor_id,
            donation_id=donation_id,
            stars=data.get("stars"),
            message=data.get("message"),
        )
        if "error" in result:
            return {"message": result["error"]}, 404
        return make_response(json_util.dumps(result), 200)

    @jwt_required()
    def delete(self, donor_id, donation_id):
        email_identity = get_jwt_identity()
        recipient = get_recipient_by_email(email_identity)
        if not recipient or email_identity != recipient.email:
            return abort(403)
        result = delete_rating(donor_id, donation_id)
        if "error" in result:
            return {"message": result["error"]}, 404
        return make_response(json_util.dumps(result), 200)


class ImpactLogResource(Resource):
    def get(self, donor_id, donation_id=None):
        if donation_id:
            donation = get_donor_impact_log_donation(donor_id, donation_id)
            if not donation:
                return {
                    "message": f"Donation with ID {donation_id} not found for donor {donor_id}"
                }, 404
            return make_response(json_util.dumps(donation), 200)
        else:
            impact_log = get_donor_impact_logs(donor_id)
            if not impact_log:
                return {"message": f"Donor with ID {donor_id} not found"}, 404
            return make_response(json_util.dumps(impact_log), 200)

    @jwt_required()
    def post(self, donor_id):
        email_identity = get_jwt_identity()
        donor = get_donor_by_email(email_identity)
        if not donor or email_identity != donor.email:
            return abort(403)
        data = request.get_json()
        required_fields = [
            "total_lbs_food",
            "lbs_food_for_consumption",
            "lbs_food_for_farms",
            "lbs_food_for_waste",
            "food_security_impact",
            "environmental_impact",
            "monetary_impact",
        ]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return {
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }, 400
        donation_data = {
            "total_lbs_food": data["total_lbs_food"],
            "lbs_food_for_consumption": data["lbs_food_for_consumption"],
            "lbs_food_for_farms": data["lbs_food_for_farms"],
            "lbs_food_for_waste": data["lbs_food_for_waste"],
            "food_security_impact": data["food_security_impact"],
            "environmental_impact": data["environmental_impact"],
            "monetary_impact": data["monetary_impact"],
        }
        donation = add_donor_impact_log(donor_id, donation_data)
        if not donation:
            return {"message": f"Donor with ID {donor_id} not found"}, 404
        return make_response(json_util.dumps(donation), 201)

    @jwt_required()
    def patch(self, donor_id, donation_id):
        email_identity = get_jwt_identity()
        donor = get_donor_by_email(email_identity)
        if not donor or email_identity != donor.email:
            return abort(403)
        data = request.get_json()
        if not data:
            return {"message": "No update data provided"}, 400
        updated_donation = update_donor_impact_log_donation(donor_id, donation_id, data)
        if "error" in updated_donation:
            return {"message": updated_donation["error"]}, 404
        return make_response(json_util.dumps(updated_donation), 200)
