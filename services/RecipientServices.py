import datetime
from .default import default_recipients
from models.Recipient import *
from mongoengine.errors import ValidationError


# Helper function for pagination
def paginate(queryset, page, pagesize):
    return queryset.skip((page - 1) * pagesize).limit(pagesize)


# Get Recipient by Email
def get_recipient_by_email(email):
    recipient = None
    if email is not None:
        recipient = Recipient.objects(email=email).first()
    return recipient


# GET /recipients
def get_all_recipients(
    page=1,
    pagesize=10,
    recipient_id=None,
    name=None,
    tax_status=None,
    compliance_status=None,
    sort_by=None,
):
    query = {}
    if recipient_id:
        query["recipient_id"] = recipient_id
    if name:
        query["$or"] = [
            {"first_name": {"$regex": name, "$options": "i"}},
            {"last_name": {"$regex": name, "$options": "i"}},
            {"organization_name": {"$regex": name, "$options": "i"}},
        ]
    if tax_status:
        query["tax_status.status"] = tax_status
    if compliance_status:
        query["compliance_status.status"] = compliance_status
    recipients = Recipient.objects(**query)
    if sort_by == "numberdonations":
        recipients = recipients.order_by("-donation_log.total_donations_received")
    recipients = paginate(recipients, page, pagesize)
    return [recipient.to_mongo().to_dict() for recipient in recipients]


# POST /recipients
def create_recipient(
    first_name,
    last_name,
    organization_name=None,
    email=None,
    phone_number=None,
    address=None,
    ein=None,
):
    try:
        address = Address(
            street_and_number=address.get("street_and_number"),
            city=address.get("city"),
            state=address.get("state"),
            zip_code=address.get("zip_code"),
            country=address.get("country"),
        )
        tax_status = TaxStatus(status="Pending", verification_date=None)
        compliance_status = ComplianceStatus(status="Pending", verification_date=None)
        recipient = Recipient(
            recipient_id=str(uuid.uuid4()),
            first_name=first_name,
            last_name=last_name,
            organization_name=organization_name,
            email=email,
            phone_number=phone_number,
            address=address,
            ein=ein,
            tax_status=tax_status,
            compliance_status=compliance_status,
            donations=[],
            donation_log=DonationLog(),
        )
        recipient.save()
        print(f"Recipient created successfully: {recipient}")
        return recipient
    except ValidationError as e:
        print(f"Validation error while creating recipient: {e}")
        raise
    except Exception as ex:
        print(f"Unexpected error while creating recipient: {ex}")
        raise


# GET /recipients/:recipientId
def get_recipient(recipient_id):
    recipient = Recipient.objects(recipient_id=recipient_id).first()
    return recipient.to_mongo().to_dict() if recipient else None


# PATCH /recipients/:recipientId
def update_recipient(
    recipient_id,
    phone_number=None,
    address=None,
    tax_status=None,
    compliance_status=None,
):
    recipient = Recipient.objects(recipient_id=recipient_id).first()
    if not recipient:
        return None
    if phone_number:
        recipient.phone_number = phone_number
    if address:
        recipient.address = Address(**address)
    if tax_status:
        recipient.tax_status.status = tax_status
        recipient.tax_status.verification_date = datetime.datetime.now()
    if compliance_status:
        recipient.compliance_status.status = compliance_status
        recipient.compliance_status.verification_date = datetime.datetime.now()
    recipient.save()
    return recipient.to_mongo().to_dict()


# DELETE /recipients/:recipientId
def delete_recipient(recipient_id):
    recipient = Recipient.objects(recipient_id=recipient_id).first()
    if not recipient:
        return None
    recipient.delete()
    return {"message": f"Recipient with ID {recipient_id} has been deleted"}


# GET /recipients/:recipientId/donationlog
def get_recipient_donation_logs(recipient_id):
    recipient = Recipient.objects(recipient_id=recipient_id).first()
    if not recipient:
        return None
    return [donation.to_mongo().to_dict() for donation in recipient.donations]


# POST /recipients/:recipientId/donationlog
def add_recipient_donation_log(recipient_id, donation_data):
    recipient = Recipient.objects(recipient_id=recipient_id).first()
    if not recipient:
        return None
    donation = Donation(**donation_data)
    recipient.donations.append(donation)
    recipient.donation_log.calculate_totals(recipient.donations)
    recipient.save()
    return donation.to_mongo().to_dict()


# GET /recipients/:recipientId/donationlog/:donationId
def get_recipient_donation_log(recipient_id, donation_id):
    recipient = Recipient.objects(recipient_id=recipient_id).first()
    if not recipient:
        return None
    donation = next(
        (d for d in recipient.donations if d.donation_id == donation_id), None
    )
    return donation.to_mongo().to_dict() if donation else None


# PATCH /recipients/:recipientId/donationlog/:donationId
def update_recipient_donation_log(recipient_id, donation_id, update_data):
    recipient = Recipient.objects(recipient_id=recipient_id).first()
    if not recipient:
        return None
    donation = next(
        (d for d in recipient.donations if d.donation_id == donation_id), None
    )
    if not donation:
        return None
    for key, value in update_data.items():
        setattr(donation, key, value)
    recipient.donation_log.calculate_totals(recipient.donations)
    recipient.save()
    return donation.to_mongo().to_dict()


# GET /recipients/:recipientId/taxexempt
def get_recipient_tax_status(recipient_id):
    recipient = Recipient.objects(recipient_id=recipient_id).first()
    if not recipient:
        return None
    return recipient.tax_status.to_mongo().to_dict()


# PATCH /recipients/:recipientId/taxexempt
def update_recipient_tax_status(recipient_id, status, verification_date):
    recipient = Recipient.objects(recipient_id=recipient_id).first()
    if not recipient:
        return None
    recipient.tax_status.status = status
    recipient.tax_status.verification_date = verification_date
    recipient.save()
    return recipient.tax_status.to_mongo().to_dict()


# GET /recipients/:recipientId/compliance
def get_recipient_compliance_status(recipient_id):
    recipient = Recipient.objects(recipient_id=recipient_id).first()
    if not recipient:
        return None
    return recipient.compliance_status.to_mongo().to_dict()


# PATCH /recipients/:recipientId/compliance
def update_recipient_compliance_status(recipient_id, status, verification_date):
    recipient = Recipient.objects(recipient_id=recipient_id).first()
    if not recipient:
        return None
    recipient.compliance_status.status = status
    recipient.compliance_status.verification_date = verification_date
    recipient.save()
    return recipient.compliance_status.to_mongo().to_dict()


# Initialize recipients
def init_recipients():
    existing_recipients = Recipient.objects()
    if existing_recipients.count() == 0:
        print("Initializing default recipients...")
        for recipient_data in default_recipients:
            try:
                print(
                    f"Preparing recipient: {recipient_data['first_name']} {recipient_data['last_name']}"
                )
                recipient = Recipient(
                    recipient_id=recipient_data["recipient_id"],
                    first_name=recipient_data["first_name"],
                    last_name=recipient_data["last_name"],
                    organization_name=recipient_data["organization_name"],
                    email=recipient_data["email"],
                    phone_number=recipient_data["phone_number"],
                    address=recipient_data["address"],
                    ein=recipient_data["ein"],
                    tax_status=recipient_data["tax_status"],
                    compliance_status=recipient_data["compliance_status"],
                    donations=recipient_data["donations"],
                    donation_log=recipient_data["donation_log"],
                )
                recipient.save()
                print(
                    f"Recipient {recipient.first_name} {recipient.last_name} saved successfully."
                )
            except Exception as e:
                print(
                    f"Error while saving recipient {recipient_data['first_name']} {recipient_data['last_name']}: {e}"
                )
        print("Default recipients have been initialized.")
    else:
        print("Recipients already exist in the database. Initialization skipped.")
