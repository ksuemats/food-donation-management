import datetime
import uuid
from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    FloatField,
    DateTimeField,
    EmbeddedDocumentField,
)


class Listing(EmbeddedDocument):
    listing_id = StringField(required=True, default=lambda: str(uuid.uuid4()))
    donation_id = StringField(required=True)
    donor_id = StringField(required=True)
    date_listed = DateTimeField(default=datetime.datetime.now, required=True)
    food_type = StringField(required=True)
    total_lbs_food = FloatField(required=True)
    refrigeration_requirements = StringField(
        required=True, choices=["None", "Refrigerated", "Frozen"]
    )
    expiration_date = DateTimeField(required=True)


class Form(EmbeddedDocument):
    form_id = StringField(required=True, default=lambda: str(uuid.uuid4()))
    donation_id = StringField(required=True)
    donor_id = StringField(required=True)
    recipient_id = StringField(required=True)
    listing_id = StringField(required=True)
    total_lbs_food = FloatField(required=True)
    lbs_expired_food = FloatField(default=0.0)
    lbs_food_for_consumption = FloatField(required=True)
    lbs_food_for_farms = FloatField(default=0.0)
    lbs_food_for_waste = FloatField(default=0.0)


class Receipt(EmbeddedDocument):
    receipt_id = StringField(required=True, default=lambda: str(uuid.uuid4()))
    donation_id = StringField(required=True)
    listing_id = StringField(required=True)
    donor_id = StringField(required=True)
    recipient_id = StringField()
    date_issued = DateTimeField(default=datetime.datetime.now, required=True)
    donation_amount_lbs = FloatField(required=True)
    donor_name = StringField(required=True)
    recipient_name = StringField(required=True)


class Donation(Document):
    donation_id = StringField(
        required=True, unique=True, default=lambda: str(uuid.uuid4())
    )
    donor_id = StringField(required=True)
    recipient_id = StringField()
    listing = EmbeddedDocumentField(Listing)
    form = EmbeddedDocumentField(Form)
    receipt = EmbeddedDocumentField(Receipt)
