from models.Donation import *
from models.Donor import *
from models.Recipient import *


default_users = {
    "karim@cmu.org": "karim",
    "ndahiya@andrew.cmu.edu": "ndahiya",
    "sydney.doe@foodbanka.org": "sydney",
    "jane.smith@charityb.org": "jane",
    "ksuemats@andrew.cmu.edu": "ksuemats",
}

default_donations = [
    {
        "donation_id": "999888",
        "donor_id": "123456",
        "listing": {
            "listing_id": "listing1",
            "donation_id": "999888",
            "donor_id": "123456",
            "date_listed": datetime.datetime.now(),
            "food_type": "Canned Goods",
            "total_lbs_food": 100,
            "refrigeration_requirements": "None",
            "expiration_date": datetime.datetime(2024, 12, 31),
        },
        "form": {
            "form_id": "form1",
            "listing_id": "listing1",
            "donation_id": "999888",
            "donor_id": "123456",
            "recipient_id": "789123",
            "total_lbs_food": 100,
            "lbs_expired_food": 0,
            "lbs_food_for_consumption": 80,
            "lbs_food_for_farms": 15,
            "lbs_food_for_waste": 5,
        },
        "receipt": {
            "receipt_id": "receipt1",
            "donation_id": "999888",
            "donor_id": "123456",
            "listing_id": "listing1",
            "date_issued": datetime.datetime.now(),
            "donation_amount_lbs": 100,
            "donor_name": "Karim Shaikh",
            "recipient_name": "Sydney Doe",
            "recipient_id": "789123",
        },
    }
]


default_donors = [
    {
        "donor_id": "123456",
        "first_name": "Karim",
        "last_name": "Shaikh",
        "email": "karim@cmu.org",
        "phone_number": "555-555-5555",
        "address": {
            "street_and_number": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "90210",
            "country": "USA",
        },
        "tax_id": "123456789",
        "company_association": "Carnegie Mellon University",
        "donations": [
            {
                "donation_id": "999888",
                "receipt_id": "receipt1",
                "total_lbs_food": 100,
                "lbs_food_for_consumption": 80,
                "lbs_food_for_farms": 15,
                "lbs_food_for_waste": 5,
                "food_security_impact": 80,
                "environmental_impact": 95,
                "monetary_impact": 100,
                "rating": {
                    "donation_id": "999888",
                    "stars": 5.0,
                    "message": "Great donation!",
                    "date": datetime.datetime.now(),
                },
            }
        ],
        "ratings": {"stars": 5.0, "total_ratings": 1},
        "impact_log": {
            "total_donations": 1,
            "total_lbs_food": 100.0,
            "total_lbs_food_for_consumption": 80.0,
            "total_lbs_food_for_farms": 15.0,
            "total_lbs_food_for_waste": 5.0,
            "total_food_security_impact": 80,
            "total_environmental_impact": 95,
            "total_monetary_impact": 100,
        },
    },
    {
        "donor_id": "456789",
        "first_name": "Nikita",
        "last_name": "Dahiya",
        "email": "ndahiya@andrew.cmu.edu",
        "phone_number": "555-555-5555",
        "address": {
            "street_and_number": "456 Elm St",
            "city": "Springfield",
            "state": "CA",
            "zip_code": "90211",
            "country": "USA",
        },
        "tax_id": "987654321",
        "company_association": "Carnegie Mellon University",
        "donations": [],
        "ratings": {"stars": 0.0, "total_ratings": 0},
        "impact_log": {
            "total_donations": 0,
            "total_lbs_food": 0.0,
            "total_lbs_food_for_consumption": 0.0,
            "total_lbs_food_for_farms": 0.0,
            "total_lbs_food_for_waste": 0.0,
            "total_food_security_impact": 0,
            "total_environmental_impact": 0.0,
            "total_monetary_impact": 0.0,
        },
    },
]


default_recipients = [
    {
        "recipient_id": "789123",
        "first_name": "Sydney",
        "last_name": "Doe",
        "organization_name": "Food Bank A",
        "email": "sydney.doe@foodbanka.org",
        "phone_number": "123-456-7890",
        "address": {
            "street_and_number": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "90210",
            "country": "USA",
        },
        "ein": "12-3456789",
        "tax_status": {
            "status": "Verified",
            "verification_date": datetime.datetime.now(),
        },
        "compliance_status": {
            "status": "In Good Standing",
            "verification_date": datetime.datetime.now(),
        },
        "donations": [
            {
                "donation_id": "999888",
                "receipt_id": "receipt1",
                "total_lbs_food": 100,
                "lbs_food_for_consumption": 80,
                "lbs_food_for_farms": 15,
                "lbs_food_for_waste": 5,
                "food_security_impact": 80,
                "environmental_impact": 95,
                "monetary_impact": 100,
            }
        ],
        "donation_log": {
            "total_donations": 1,
            "total_lbs_food": 100.0,
            "total_lbs_food_for_consumption": 80.0,
            "total_lbs_food_for_farms": 15.0,
            "total_lbs_food_for_waste": 5.0,
            "total_food_security_impact": 80,
            "total_environmental_impact": 95.0,
            "total_monetary_impact": 100.0,
        },
    },
    {
        "recipient_id": "987654",
        "first_name": "Jane",
        "last_name": "Smith",
        "organization_name": "Charity B",
        "email": "jane.smith@charityb.org",
        "phone_number": "987-654-3210",
        "address": {
            "street_and_number": "456 Elm St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "90211",
            "country": "USA",
        },
        "ein": "98-7654321",
        "tax_status": {
            "status": "Pending",
            "verification_date": datetime.datetime.now(),
        },
        "compliance_status": {
            "status": "At Risk",
            "verification_date": datetime.datetime.now(),
        },
        "donations": [],
        "donation_log": {
            "total_donations": 0,
            "total_lbs_food": 0.0,
            "total_lbs_food_for_consumption": 0.0,
            "total_lbs_food_for_farms": 0.0,
            "total_lbs_food_for_waste": 0.0,
            "total_food_security_impact": 0,
            "total_environmental_impact": 0.0,
            "total_monetary_impact": 0.0,
        },
    },
]
