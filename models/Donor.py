import datetime
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


class RatingDetails(EmbeddedDocument):
    donation_id = StringField()
    stars = IntField(min_value=1, max_value=5)
    message = StringField()
    date = DateTimeField(default=datetime.datetime.now)


class Ratings(EmbeddedDocument):
    stars = FloatField(default=0.0)
    total_ratings = IntField(default=0)

    def update_ratings(self, stars):
        self.total_ratings += 1
        self.stars = (
            (self.stars * (self.total_ratings - 1)) + stars
        ) / self.total_ratings


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
    rating = EmbeddedDocumentField(RatingDetails, default=None)


class ImpactLog(EmbeddedDocument):
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


class Donor(Document):
    donor_id = StringField(
        required=True, unique=True, default=lambda: str(uuid.uuid4())
    )
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    email = StringField(required=True)
    phone_number = StringField(required=True)
    tax_id = StringField(required=True)
    company_association = StringField(required=True)
    address = EmbeddedDocumentField(Address, default=Address)
    donations = EmbeddedDocumentListField(Donation, default=list)
    ratings = EmbeddedDocumentField(Ratings, default=Ratings)
    ratings_details = EmbeddedDocumentListField(RatingDetails, default=list)
    impact_log = EmbeddedDocumentField(ImpactLog, default=ImpactLog)

    def update_impact_log(self):
        self.impact_log.calculate_totals(self.donations)
