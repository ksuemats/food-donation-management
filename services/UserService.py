from .default import default_users
from models.User import User
from utils.Hash import get_hash


def create_user(email: str, password_hash: str):
    new_user = User(email=email, password_hash=password_hash)
    new_user.save()


def find_user_by_email(email: str):
    return User.objects.filter(email=email).first()


def delete_user(email: str):
    user = User.objects.filter(email=email).first()
    if not user:
        return None
    user.delete()
    return {"message": f"User with email {email} has been deleted"}


def init_users():
    existing_users = User.objects()
    if len(existing_users) == 0:
        for user_email in default_users:
            password_hash = get_hash(default_users[user_email].encode('utf-8'))
            create_user(user_email, password_hash)
