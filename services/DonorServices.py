import datetime
from .default import default_donors
from models.Donor import *
from mongoengine.errors import ValidationError


# Helper function for pagination
def paginate(queryset, page, pagesize):
    start = (page - 1) * pagesize
    return queryset.skip(start).limit(pagesize)


# Get Donor by Email
def get_donor_by_email(email):
    donor = None
    if email is not None:
        donor = Donor.objects(email=email).first()
    return donor


# GET /donors
def get_all_donors(
    page=1, pagesize=10, donor_id=None, name=None, email=None, sort_by=None
):
    query = {}
    if donor_id:
        query["donor_id"] = donor_id
    if name:
        query["$or"] = [
            {"first_name": {"$regex": name, "$options": "i"}},
            {"last_name": {"$regex": name, "$options": "i"}},
        ]
    if email:
        query["email"] = {"$regex": email, "$options": "i"}
    print(f"Constructed Query: {query}")
    donors = Donor.objects(**query)
    if sort_by == "numberdonations":
        donors = donors.order_by("-impact_log.total_donations")
    donors = paginate(donors, page, pagesize)
    print(f"Number of donors retrieved: {donors.count()}")
    return [donor.to_mongo().to_dict() for donor in donors]


# POST /donors
def create_donor(
    first_name, last_name, email, phone_number, address, tax_id, company_association
):
    try:
        address = Address(
            street_and_number=address.get("street_and_number"),
            city=address.get("city"),
            state=address.get("state"),
            zip_code=address.get("zip_code"),
            country=address.get("country"),
        )
        donor = Donor(
            donor_id=str(uuid.uuid4()),
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            address=address,
            tax_id=tax_id,
            company_association=company_association,
            donations=[],
            ratings=Ratings(),
            impact_log=ImpactLog(),
        )
        donor.save()
        print(f"Donor created successfully: {donor}")
        return donor
    except ValidationError as e:
        print(f"Validation error while creating donor: {e}")
        raise
    except Exception as ex:
        print(f"Unexpected error while creating donor: {ex}")
        raise


# GET /donors/:donorId
def get_donor(donor_id):
    donor = Donor.objects(donor_id=donor_id).first()
    return donor.to_mongo().to_dict() if donor else None


# PATCH /donors/:donorId
def update_donor(donor_id, phone_number=None, address=None, company_association=None):
    donor = Donor.objects(donor_id=donor_id).first()
    if not donor:
        return None
    if phone_number:
        donor.phone_number = phone_number
    if address:
        donor.address = Address(**address)
    if company_association:
        donor.company_association = company_association
    donor.save()
    return donor.to_mongo().to_dict()


# DELETE /donors/:donorId
def delete_donor(donor_id):
    donor = Donor.objects(donor_id=donor_id).first()
    if not donor:
        return None
    donor.delete()
    return {"message": f"Donor with ID {donor_id} has been deleted"}


# GET /donors/:donorId/ratings
def get_ratings(donor_id):
    donor = Donor.objects(donor_id=donor_id).first()
    if not donor:
        return {"error": f"Donor with ID {donor_id} not found"}
    return donor.ratings.to_mongo().to_dict()


# POST /donors/:donorId/ratings
def create_rating(donor_id, donation_id, stars, message=None):
    donor = Donor.objects(donor_id=donor_id).first()
    if not donor:
        return {"error": f"Donor with ID {donor_id} not found"}
    donation = next((d for d in donor.donations if d.donation_id == donation_id), None)
    if not donation:
        return {
            "error": f"Donation with ID {donation_id} not found for donor {donor_id}"
        }
    donation.rating = RatingDetails(
        donation_id=donation_id,
        stars=stars,
        message=message,
        date=datetime.datetime.now(),
    )
    donor.ratings.update_ratings(stars)
    donor.save()
    return {
        "message": "Rating created successfully",
        "ratings": donor.ratings.to_mongo().to_dict(),
    }


# PATCH /donors/:donorId/ratings/:donationId
def update_rating(donor_id, donation_id, stars=None, message=None):
    donor = Donor.objects(donor_id=donor_id).first()
    if not donor:
        return {"error": f"Donor with ID {donor_id} not found"}
    donation = next((d for d in donor.donations if d.donation_id == donation_id), None)
    if not donation:
        return {
            "error": f"Donation with ID {donation_id} not found for donor {donor_id}"
        }
    if donation.rating:
        previous_stars = donation.rating.stars
        if stars is not None:
            donation.rating.stars = stars
            donor.ratings.stars = (
                (donor.ratings.stars * donor.ratings.total_ratings)
                - previous_stars
                + stars
            ) / donor.ratings.total_ratings
        if message is not None:
            donation.rating.message = message
        donation.rating.date = datetime.datetime.now()
    else:
        return {"error": f"No existing rating for donation ID {donation_id}"}
    donor.save()
    return {
        "message": "Rating updated successfully",
        "ratings": donor.ratings.to_mongo().to_dict(),
        "updated_rating": donation.rating.to_mongo().to_dict(),
    }


# DELETE /donors/:donorId/ratings/:donationId
def delete_rating(donor_id, donation_id):
    donor = Donor.objects(donor_id=donor_id).first()
    if not donor:
        return {"error": f"Donor with ID {donor_id} not found"}
    donation = next((d for d in donor.donations if d.donation_id == donation_id), None)
    if not donation:
        return {
            "error": f"Donation with ID {donation_id} not found for donor {donor_id}"
        }
    if donation.rating:
        previous_stars = donation.rating.stars
        donation.rating = None
        if donor.ratings.total_ratings > 1:
            donor.ratings.stars = (
                (donor.ratings.stars * donor.ratings.total_ratings) - previous_stars
            ) / (donor.ratings.total_ratings - 1)
        else:
            donor.ratings.stars = 0.0
        donor.ratings.total_ratings -= 1
        donor.ratings_details = [
            rating
            for rating in donor.ratings_details
            if rating.date != donation.rating.date
        ]
    else:
        return {"error": f"No existing rating for donation ID {donation_id}"}
    donor.save()
    return {
        "message": "Rating deleted successfully",
        "ratings": donor.ratings.to_mongo().to_dict(),
    }


# GET /donors/:donorId/impactlog
def get_donor_impact_logs(donor_id):
    donor = Donor.objects(donor_id=donor_id).first()
    if not donor:
        return None
    return donor.impact_log.to_mongo().to_dict()


# POST /donors/:donorId/impactlog
def add_donor_impact_log(donor_id, donation_data):
    donor = Donor.objects(donor_id=donor_id).first()
    if not donor:
        return None
    donation = Donation(**donation_data)
    donor.donations.append(donation)
    donor.impact_log.calculate_totals(donor.donations)
    donor.save()
    return donation.to_mongo().to_dict()


# GET /donors/:donorId/impactlog/:donationId
def get_donor_impact_log_donation(donor_id, donation_id):
    donor = Donor.objects(donor_id=donor_id).first()
    if not donor:
        return {"error": f"Donor with ID {donor_id} not found"}
    donation = next((d for d in donor.donations if d.donation_id == donation_id), None)
    if not donation:
        return {
            "error": f"Donation with ID {donation_id} not found for donor {donor_id}"
        }
    return donation.to_mongo().to_dict()


# PATCH /donors/:donorId/impactlog/:donationId
def update_donor_impact_log_donation(donor_id, donation_id, update_data):
    donor = Donor.objects(donor_id=donor_id).first()
    if not donor:
        return {"error": f"Donor with ID {donor_id} not found"}
    donation = next(
        (d for d in donor.donations if str(d.donation_id) == str(donation_id)), None
    )
    if not donation:
        return {
            "error": f"Donation with ID {donation_id} not found for donor {donor_id}"
        }
    for key, value in update_data.items():
        if hasattr(donation, key):
            setattr(donation, key, value)
        else:
            return {"error": f"Invalid field '{key}' for donation"}
    donation.donation_id = str(donation.donation_id)
    donor.impact_log.calculate_totals(donor.donations)
    print(f"Donor before save: {donor.to_mongo().to_dict()}")
    donor.save()
    return {
        "message": "Donation updated successfully",
        "donation": donation.to_mongo().to_dict(),
    }


# Initialize default donors
def init_donors():
    existing_donors = Donor.objects()
    if existing_donors.count() == 0:
        print("Initializing default donors...")
        for donor_data in default_donors:
            try:
                print(
                    f"Preparing donor: {donor_data['first_name']} {donor_data['last_name']}"
                )
                donor = Donor(
                    donor_id=donor_data["donor_id"],
                    first_name=donor_data["first_name"],
                    last_name=donor_data["last_name"],
                    email=donor_data["email"],
                    phone_number=donor_data["phone_number"],
                    address=donor_data["address"],
                    tax_id=donor_data["tax_id"],
                    company_association=donor_data["company_association"],
                    donations=donor_data["donations"],
                    impact_log=donor_data["impact_log"],
                    ratings=donor_data["ratings"],
                )
                donor.save()
                print(f"Donor {donor.first_name} {donor.last_name} saved successfully.")
            except Exception as e:
                print(
                    f"Error while saving donor {donor_data['first_name']} {donor_data['last_name']}: {e}"
                )
        print("Default donors have been initialized.")
    else:
        print("Donors already exist in the database. Initialization skipped.")
