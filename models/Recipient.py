import uuid
from mongoengine import (
    Document,
    StringField,
    FloatField,
    IntField,
    DateTimeField,
    EmbeddedDocumentField,
    EmbeddedDocument,
    EmbeddedDocumentListField,
)


class Address(EmbeddedDocument):
    street_and_number = StringField()
    city = StringField()
    state = StringField()
    zip_code = StringField()
    country = StringField()


class Donation(EmbeddedDocument):
    donation_id = StringField(default=lambda: str(uuid.uuid4()))
    receipt_id = StringField(default=lambda: str(uuid.uuid4()))
    total_lbs_food = FloatField(default=0.0)
    lbs_food_for_consumption = FloatField(default=0.0)
    lbs_food_for_farms = FloatField(default=0.0)
    lbs_food_for_waste = FloatField(default=0.0)
    food_security_impact = IntField(default=0)
    environmental_impact = FloatField(default=0.0)
    monetary_impact = FloatField(default=0.0)


class DonationLog(EmbeddedDocument):
    total_donations = IntField(default=0)
    total_lbs_food = FloatField(default=0.0)
    total_lbs_food_for_consumption = FloatField(default=0.0)
    total_lbs_food_for_farms = FloatField(default=0.0)
    total_lbs_food_for_waste = FloatField(default=0.0)
    total_food_security_impact = IntField(default=0)
    total_environmental_impact = FloatField(default=0.0)
    total_monetary_impact = FloatField(default=0.0)

    def calculate_totals(self, donations):
        self.total_donations = len(donations)
        self.total_lbs_food = sum(donation.total_lbs_food for donation in donations)
        self.total_lbs_food_for_consumption = sum(
            donation.lbs_food_for_consumption for donation in donations
        )
        self.total_lbs_food_for_farms = sum(
            donation.lbs_food_for_farms for donation in donations
        )
        self.total_lbs_food_for_waste = sum(
            donation.lbs_food_for_waste for donation in donations
        )
        self.total_food_security_impact = sum(
            donation.food_security_impact for donation in donations
        )
        self.total_environmental_impact = sum(
            donation.environmental_impact for donation in donations
        )
        self.total_monetary_impact = sum(
            donation.monetary_impact for donation in donations
        )


class TaxStatus(EmbeddedDocument):
    status = StringField(required=False)
    verification_date = DateTimeField(required=False)


class ComplianceStatus(EmbeddedDocument):
    status = StringField(required=False)
    verification_date = DateTimeField(required=False)


class Recipient(Document):
    recipient_id = StringField(
        required=True, unique=True, default=lambda: str(uuid.uuid4())
    )
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    organization_name = StringField(required=True)
    email = StringField(required=True)
    phone_number = StringField(required=True)
    address = EmbeddedDocumentField(Address)
    ein = StringField(required=True)
    tax_status = EmbeddedDocumentField(TaxStatus, required=True)
    compliance_status = EmbeddedDocumentField(ComplianceStatus, required=True)
    donations = EmbeddedDocumentListField(Donation)
    donation_log = EmbeddedDocumentField(DonationLog, default=DonationLog)
