import datetime
import uuid
from .default import default_donations
from models.Donation import Donation, Listing, Form, Receipt
from mongoengine.errors import ValidationError


# Helper function for pagination
def paginate(queryset, page, pagesize):
    return queryset.skip((page - 1) * pagesize).limit(pagesize)


# GET /donations/listings
def get_all_listings(page=1, pagesize=10, food_type=None, expiration_date=None, sort_by=None):
    query = {}
    if food_type:
        query["listing.food_type"] = food_type
    if expiration_date:
        query["listing.expiration_date__lte"] = datetime.datetime.strptime(expiration_date, '%Y-%m-%d')
    
    donations = Donation.objects(**query)
    if sort_by == "date_listed":
        donations = donations.order_by("listing.date_listed")
    elif sort_by == "total_lbs_food":
        donations = donations.order_by("-listing.total_lbs_food")

    # Paginate results
    start = (page - 1) * pagesize
    end = start + pagesize
    paginated_listings = donations[start:end]
    return [donation.listing.to_mongo().to_dict() for donation in paginated_listings if donation.listing]


# POST /donations/listings
def create_listing(donor_id, listing_data):
    try:
        refrigeration_requirements = listing_data.get(
            "refrigeration_requirements"
        ).capitalize()
        valid_requirements = ["None", "Refrigerated", "Frozen"]
        if refrigeration_requirements not in valid_requirements:
            raise ValueError(
                f"Invalid refrigeration requirement: {refrigeration_requirements}. Must be one of {valid_requirements}."
            )
        listing = Listing(
            listing_id=str(uuid.uuid4()),
            donation_id=listing_data.get("donation_id", str(uuid.uuid4())),
            donor_id=donor_id,
            date_listed=listing_data.get("date_listed"),
            food_type=listing_data.get("food_type"),
            total_lbs_food=listing_data.get("total_lbs_food"),
            refrigeration_requirements=refrigeration_requirements,
            expiration_date=listing_data.get("expiration_date"),
        )
        donation = Donation(
            donation_id=listing.donation_id, donor_id=donor_id, listing=listing
        )
        donation.save()
        print(f"Listing created successfully: {listing}")
        return listing
    except ValidationError as e:
        print(f"Validation error while creating listing: {e}")
        raise
    except Exception as ex:
        print(f"Unexpected error while creating listing: {ex}")
        raise


# PATCH /donations/listings/:listingId
def update_listing(
    listing_id,
    food_type=None,
    total_lbs_food=None,
    refrigeration_requirements=None,
    expiration_date=None,
):
    try:
        donation = Donation.objects(listing__listing_id=listing_id).first()
        if not donation or not donation.listing:
            return None
        listing = donation.listing
        if food_type is not None:
            listing.food_type = food_type
        if total_lbs_food is not None:
            listing.total_lbs_food = total_lbs_food
        if refrigeration_requirements is not None:
            valid_requirements = ["None", "Refrigerated", "Frozen"]
            if refrigeration_requirements.capitalize() not in valid_requirements:
                raise ValueError(
                    f"Invalid refrigeration requirement. Must be one of {valid_requirements}."
                )
            listing.refrigeration_requirements = refrigeration_requirements.capitalize()
        if expiration_date is not None:
            listing.expiration_date = (
                datetime.datetime.strptime(expiration_date, "%Y-%m-%d")
                if isinstance(expiration_date, str)
                else expiration_date
            )
        donation.listing = listing
        donation.save()
        return listing
    except ValidationError as e:
        print(f"Validation error while updating listing: {e}")
        raise
    except Exception as ex:
        print(f"Unexpected error while updating listing: {ex}")
        raise


# DELETE /donations/listings/:listingId
def delete_listing(listing_id):
    try:
        donation = Donation.objects(listing__listing_id=listing_id).first()
        if not donation or not donation.listing:
            return None
        donation.listing = None
        donation.save()
        return {
            "message": f"Listing with ID {listing_id} has been deleted successfully"
        }
    except Exception as ex:
        print(f"Unexpected error while deleting listing {listing_id}: {ex}")
        raise


# GET /donations/listings/:listingId/forms
def get_all_forms(listing_id):
    donation = Donation.objects(listing__listing_id=listing_id).first()
    if donation and donation.form:
        return donation.form.to_mongo().to_dict()
    return None


# POST /donations/listings/:listingId/forms
def create_form(donor_id, listing_id, form_data):
    try:
        form = Form(
            form_id=form_data.get("form_id"),
            listing_id=listing_id,
            donation_id=form_data.get("donation_id"),
            donor_id=donor_id,
            recipient_id=form_data.get("recipient_id"),
            total_lbs_food=form_data.get("total_lbs_food"),
            lbs_expired_food=form_data.get("lbs_expired_food"),
            lbs_food_for_consumption=form_data.get("lbs_food_for_consumption"),
            lbs_food_for_farms=form_data.get("lbs_food_for_farms"),
            lbs_food_for_waste=form_data.get("lbs_food_for_waste"),
        )
        donation = Donation.objects(
            donor_id=donor_id, listing__listing_id=listing_id
        ).first()
        if not donation:
            return None
        donation.form = form
        receipt = Receipt(
            receipt_id=str(uuid.uuid4()),
            listing_id=listing_id,
            donation_id=donation.form.donation_id,
            donor_id=donor_id,
            recipient_id=form.recipient_id,
            date_issued=datetime.datetime.now(),
            donation_amount_lbs=form.total_lbs_food,
            donor_name=form_data.get("donor_name"),
            recipient_name=form_data.get("recipient_name"),
        )
        donation.receipt = receipt
        donation.save()
        return {"form": form, "receipt": receipt}
    except ValidationError as e:
        print(f"Validation error while creating form: {e}")
        raise
    except Exception as ex:
        print(f"Unexpected error while creating form: {ex}")
        raise


def update_form(listing_id, form_id, update_data):
    donation = Donation.objects(listing__listing_id=listing_id).first()
    if not donation or not donation.form or donation.form.form_id != form_id:
        return None
    form = donation.form
    for field, value in update_data.items():
        if hasattr(form, field) and value is not None:
            setattr(form, field, value)
    receipt = donation.receipt
    if receipt:
        receipt.donation_amount_lbs = form.total_lbs_food
        receipt.date_issued = datetime.datetime.now()
    donation.save()
    return {"form": form, "receipt": receipt}


def delete_form(listing_id):
    donation = Donation.objects(listing__listing_id=listing_id).first()
    if not donation or not donation.form:
        return None
    form_data = donation.form.to_mongo().to_dict()
    donation.form = None
    donation.save()
    return form_data


# GET /donations/listings/:listingId/receipts
def get_receipts(listing_id):
    donation = Donation.objects(listing__listing_id=listing_id).first()
    if donation and donation.receipt:
        return donation.receipt
    return None


# POST /donations/listings/:listingId/receipts
def create_receipt(donor_id, listing_id, receipt_data):
    try:
        receipt = Receipt(
            receipt_id=receipt_data.get("receipt_id"),
            listing_id=listing_id,
            donation_id=receipt_data.get("donation_id"),
            donor_id=donor_id,
            date_issued=receipt_data.get("date_issued"),
            donation_amount_lbs=receipt_data.get("donation_amount_lbs"),
            donor_name=receipt_data.get("donor_name"),
            recipient_name=receipt_data.get("recipient_name"),
            recipient_id=receipt_data.get("recipient_id"),
        )
        donation = Donation.objects(
            donor_id=donor_id, listing__listing_id=listing_id
        ).first()
        if not donation:
            return None
        donation.receipt = receipt
        donation.save()
        return receipt
    except ValidationError as e:
        print(f"Validation error while creating receipt: {e}")
        raise
    except Exception as ex:
        print(f"Unexpected error while creating receipt: {ex}")
        raise


# GET /donations/receipts
def get_all_receipts(
    page=1, pagesize=10, donor_id=None, recipient_id=None, sort_by=None
):
    query = {}
    if donor_id:
        query["receipt.donor_id"] = donor_id
    if recipient_id:
        query["receipt.recipient_id"] = recipient_id
    donations = Donation.objects(__raw__=query)
    receipts = [
        donation.receipt.to_mongo().to_dict()
        for donation in donations
        if donation.receipt
    ]
    if sort_by == "date_issued":
        receipts.sort(key=lambda x: x.date_issued, reverse=True)
    elif sort_by == "donation_amount":
        receipts.sort(key=lambda x: x.donation_amount_lbs, reverse=True)
    start = (page - 1) * pagesize
    end = start + pagesize
    paginated_receipts = receipts[start:end]
    return [receipt for receipt in paginated_receipts]


# GET /donations/receipts/:receiptId
def get_receipt_by_id(receipt_id):
    donation = Donation.objects(receipt__receipt_id=receipt_id).first()
    receipt = (
        donation.receipt.to_mongo().to_dict() if donation and donation.receipt else None
    )
    return receipt


# GET /donations/:donationId
def get_donation_by_id(donation_id):
    donation = Donation.objects(donation_id=donation_id).first()
    return donation.to_mongo().to_dict() if donation else None


def init_donations():
    existing_donations = Donation.objects()
    if existing_donations.count() == 0:
        print("Initializing default donations...")
        for donation_data in default_donations:
            try:
                print(f"Preparing donation: {donation_data['donation_id']}")
                donation = Donation(
                    donation_id=donation_data["donation_id"],
                    donor_id=donation_data["donor_id"],
                    listing=donation_data["listing"],
                    form=donation_data["form"],
                    receipt=donation_data["receipt"],
                )
                donation.save()
                print(f"Donation {donation.donation_id} saved successfully.")
            except Exception as e:
                print(
                    f"Error while saving donation {donation_data['donation_id']}: {e}"
                )
        print("Donations initialized successfully.")
    else:
        print("Donations already exist in the database. Initialization skipped.")
