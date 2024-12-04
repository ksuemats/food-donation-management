import datetime
from bson import json_util
from flask import abort, make_response, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse
from services.DonationServices import *
from services.DonorServices import *
from services.RecipientServices import * 
from models.Donation import Donation


headers = {"Content-Type": "application/json"}

# Define parsers for request validation
listing_post_parser = reqparse.RequestParser()
listing_post_parser.add_argument(
    "food_type", type=str, required=True, help="Food Type is required"
)
listing_post_parser.add_argument(
    "total_lbs_food", type=int, required=True, help="Total Lbs of Food is required"
)
listing_post_parser.add_argument(
    "refrigeration_requirements",
    type=str,
    required=True,
    help="Refrigeration Requirements are required",
)
listing_post_parser.add_argument(
    "expiration_date", type=str, required=True, help="Expiration Date is required"
)

form_post_parser = reqparse.RequestParser()
form_post_parser.add_argument(
    "total_lbs_food", type=int, required=True, help="Total Lbs of Food is required"
)
form_post_parser.add_argument(
    "lbs_expired_food", type=int, required=True, help="Lbs of Expired Food is required"
)
form_post_parser.add_argument(
    "lbs_food_for_consumption",
    type=int,
    required=True,
    help="Lbs of Food for Consumption is required",
)
form_post_parser.add_argument(
    "lbs_food_for_farms",
    type=int,
    required=True,
    help="Lbs of Food for Farms is required",
)
form_post_parser.add_argument(
    "lbs_food_for_waste",
    type=int,
    required=True,
    help="Lbs of Food for Waste is required",
)
form_post_parser.add_argument(
    "donor_first_name", type=str, required=True, help="Donor first name is required"
)
form_post_parser.add_argument(
    "donor_last_name", type=str, required=True, help="Donor last name is required"
)
form_post_parser.add_argument(
    "recipient_first_name",
    type=str,
    required=True,
    help="Recipient first name is required",
)
form_post_parser.add_argument(
    "recipient_last_name",
    type=str,
    required=True,
    help="Recipient last name is required",
)

receipt_post_parser = reqparse.RequestParser()
receipt_post_parser.add_argument(
    "donation_amount_lbs",
    type=int,
    required=True,
    help="Donation Amount (Lbs) is required",
)
receipt_post_parser.add_argument(
    "donor_name", type=str, required=True, help="Donor Name is required"
)
receipt_post_parser.add_argument(
    "recipient_name", type=str, required=True, help="Recipient Name is required"
)
receipt_post_parser.add_argument("recipient_id", type=str, required=False)


class DonationListingResource(Resource):
    def serialize_datetime(self, obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, datetime.datetime):
                    obj[key] = value.isoformat()
        return obj

    def get(self, listing_id=None):
        if listing_id:
            print(Donation)
            donation = Donation.objects(listing__listing_id=listing_id).first()
            if not donation or not donation.listing:
                return {"message": f"Listing with ID {listing_id} not found"}, 404
            return jsonify(
                self.serialize_datetime(donation.listing.to_mongo().to_dict())
            )
        else:
            args = request.args
            page = int(args.get("page", 1))
            pagesize = int(args.get("pagesize", 10))
            food_type = args.get("food_type")
            expiration_date = args.get("expiration_date")
            sort_by = args.get("sort_by")
            listings = get_all_listings(
                page, pagesize, food_type, expiration_date, sort_by
            )
            return jsonify([self.serialize_datetime(listing) for listing in listings])

    @jwt_required()
    def post(self):
        email_identity = get_jwt_identity()
        donor = get_donor_by_email(email_identity)
        if donor and email_identity != donor.email:
            return abort(403)
        donor_id = donor.donor_id
        args = listing_post_parser.parse_args()
        valid_requirements = ["None", "Refrigerated", "Frozen"]
        refrigeration_requirements = args.refrigeration_requirements.capitalize()
        if refrigeration_requirements not in valid_requirements:
            return {
                "message": f"Invalid refrigeration requirement. Must be one of {valid_requirements}"
            }, 400
        try:
            listing_data = {
                "date_listed": datetime.datetime.now(),
                "food_type": args.food_type,
                "total_lbs_food": args.total_lbs_food,
                "refrigeration_requirements": refrigeration_requirements,
                "expiration_date": datetime.datetime.strptime(
                    args.expiration_date, "%Y-%m-%d"
                ),
            }
            listing = create_listing(donor_id, listing_data)
            return make_response(
                json_util.dumps(listing.to_mongo().to_dict()), 201, headers
            )
        except ValueError as e:
            return {"message": str(e)}, 400
        except Exception as e:
            print(f"Unexpected error while creating listing: {e}")
            return {
                "message": "An unexpected error occurred while creating the listing"
            }, 500

    @jwt_required()
    def patch(self, listing_id):
        email_identity = get_jwt_identity()
        donor = get_donor_by_email(email_identity)
        if not donor or email_identity != donor.email:
            return abort(403)
        data = request.get_json()
        listing = update_listing(
            listing_id=listing_id,
            food_type=data.get("food_type"),
            total_lbs_food=data.get("total_lbs_food"),
            refrigeration_requirements=data.get("refrigeration_requirements"),
            expiration_date=data.get("expiration_date"),
        )
        if not listing:
            return make_response(
                {"error": f"Listing with ID {listing_id} not found"}, 404
            )
        return make_response(json_util.dumps(listing.to_mongo().to_dict()), 200)

    @jwt_required()
    def delete(self, listing_id):
        email_identity = get_jwt_identity()
        donor = get_donor_by_email(email_identity)
        if not donor or email_identity != donor.email:
            return abort(403)
        listing = delete_listing(listing_id)
        if not listing:
            return make_response(
                {"error": f"Listing with ID {listing_id} not found"}, 404
            )
        return make_response(json_util.dumps(listing), 200)


class DonationFormResource(Resource):
    def serialize_datetime(self, obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, datetime.datetime):
                    obj[key] = value.isoformat()
        return obj

    def get(self, listing_id):
        donation = Donation.objects(listing__listing_id=listing_id).first()
        if not donation or not donation.listing:
            return {"message": f"Listing with ID {listing_id} not found"}, 404
        if not donation.form:
            return {"message": f"No form found for Listing ID {listing_id}"}, 404
        return make_response(
            json_util.dumps(donation.form.to_mongo().to_dict()), 200, headers
        )

    @jwt_required()
    def post(self, listing_id):
        email_identity = get_jwt_identity()
        recipient = get_recipient_by_email(email_identity)
        if not recipient or email_identity != recipient.email:
            return abort(403)
        args = form_post_parser.parse_args()
        recipient_id = recipient.recipient_id
        donation = Donation.objects(listing__listing_id=listing_id).first()
        if not donation:
            return {"message": f"Listing with ID {listing_id} not found"}, 404
        form_data = {
            "form_id": str(uuid.uuid4()),
            "listing_id": listing_id,
            "donation_id": donation.donation_id,
            "recipient_id": recipient_id,
            "donor_id": donation.donor_id,
            "total_lbs_food": args.total_lbs_food,
            "lbs_expired_food": args.lbs_expired_food,
            "lbs_food_for_consumption": args.lbs_food_for_consumption,
            "lbs_food_for_farms": args.lbs_food_for_farms,
            "lbs_food_for_waste": args.lbs_food_for_waste,
            "donor_name": f"{args.donor_first_name} {args.donor_last_name}",
            "recipient_name": f"{args.recipient_first_name} {args.recipient_last_name}",
        }
        try:
            form = create_form(donation.donor_id, listing_id, form_data)
            if not form:
                return {
                    "message": f"Form creation failed for Listing ID {listing_id}"
                }, 404
            return make_response(
                json_util.dumps(form.get("form").to_mongo().to_dict()), 201
            )
        except ValidationError as e:
            return {"message": f"Validation error: {str(e)}"}, 400
        except Exception as e:
            return {
                "message": f"An error occurred while creating the form: {str(e)}"
            }, 500

    @jwt_required()
    def patch(self, listing_id, form_id):
        email_identity = get_jwt_identity()
        recipient = get_recipient_by_email(email_identity)
        if not recipient or email_identity != recipient.email:
            return abort(403)
        data = request.get_json()
        try:
            form = update_form(listing_id, form_id, data)
            if not form:
                return {
                    "message": f"No form found for Form ID {form_id} in Listing ID {listing_id}"
                }, 404
            return make_response(
                json_util.dumps(form.get("form").to_mongo().to_dict()), 200
            )
        except ValidationError as e:
            return {"message": f"Validation error: {str(e)}"}, 400
        except Exception as e:
            return {
                "message": f"An error occurred while updating the form: {str(e)}"
            }, 500

    @jwt_required()
    def delete(self, listing_id, form_id):
        email_identity = get_jwt_identity()
        recipient = get_recipient_by_email(email_identity)
        if not recipient or email_identity != recipient.email:
            return abort(403)
        try:
            deleted_form = delete_form(listing_id)
            if not deleted_form:
                return {
                    "message": f"No form found for Form ID {form_id} in Listing ID {listing_id}"
                }, 404
            return make_response(
                {
                    "message": f"Form for Form ID {form_id} in Listing ID {listing_id} deleted successfully"
                },
                200,
            )
        except Exception as e:
            return {
                "message": f"An error occurred while deleting the form: {str(e)}"
            }, 500


class DonationReceiptResource(Resource):
    def get(self, listing_id):
        try:
            receipt = get_receipts(listing_id)
            if not receipt:
                return {"message": f"No receipt found for Listing ID {listing_id}"}, 404
            return make_response(json_util.dumps(receipt.to_mongo().to_dict()), 200)
        except Exception as e:
            return {
                "message": f"An error occurred while retrieving the receipt: {str(e)}"
            }, 500

    @jwt_required()
    def post(self, listing_id):
        email_identity = get_jwt_identity()
        donor = get_donor_by_email(email_identity)
        if not donor or email_identity != donor.email:
            return abort(403)
        donor_id = donor.donor_id
        data = request.get_json()
        receipt_data = {
            "receipt_id": str(uuid.uuid4()),
            "donation_id": data.get("donation_id"),
            "date_issued": datetime.datetime.now(),
            "donation_amount_lbs": data.get("donation_amount_lbs"),
            "donor_name": data.get("donor_name"),
            "recipient_name": data.get("recipient_name"),
            "recipient_id": data.get("recipient_id"),
        }
        try:
            receipt = create_receipt(donor_id, listing_id, receipt_data)
            if not receipt:
                return {"message": f"Listing with ID {listing_id} not found"}, 404
            return make_response(json_util.dumps(receipt.to_mongo().to_dict()), 201)
        except ValidationError as e:
            return {"message": f"Validation error: {str(e)}"}, 400
        except Exception as e:
            print(f"Unexpected error while creating receipt: {e}")
            return {
                "message": "An unexpected error occurred while creating the receipt"
            }, 500


class ReceiptResource(Resource):
    def get(self):
        try:
            args = request.args
            page = int(args.get("page", 1))
            pagesize = int(args.get("pagesize", 10))
            donor_id = args.get("donorid")
            recipient_id = args.get("recipientid")
            sort_by = args.get("sort_by")
            receipts = get_all_receipts(page, pagesize, donor_id, recipient_id, sort_by)
            if not receipts:
                return {"message": "No receipts found"}, 404
            return make_response(json_util.dumps(receipts), 200)
        except Exception as e:
            return {
                "message": f"An error occurred while retrieving receipts: {str(e)}"
            }, 500


class ReceiptDetailResource(Resource):
    def get(self, receipt_id):
        try:
            receipt = get_receipt_by_id(receipt_id)
            if not receipt:
                return {"message": f"Receipt with ID {receipt_id} not found"}, 404
            return make_response(json_util.dumps(receipt), 200)
        except Exception as e:
            return {
                "message": f"An error occurred while retrieving the receipt: {str(e)}"
            }, 500


class DonationDetailResource(Resource):
    def get(self, donation_id):
        try:
            donation = get_donation_by_id(donation_id)
            if not donation:
                return {"message": f"Donation with ID {donation_id} not found"}, 404
            return make_response(json_util.dumps(donation), 200)
        except Exception as e:
            return {
                "message": f"An error occurred while retrieving the donation: {str(e)}"
            }, 500
