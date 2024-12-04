from flask_mongoengine import MongoEngine
from services.DonationServices import init_donations
from services.DonorServices import init_donors
from services.RecipientServices import init_recipients
from services.UserService import init_users


db = MongoEngine()


def initialize_db(app):
    db.init_app(app)
    init_donations()
    init_donors()
    init_recipients()
    init_users()


def fetch_engine():
    return db
