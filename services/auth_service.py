import os
import hashlib
import random
import threading

from SQL_ORM import User, App_ORM, Verification_info
from services.email_service import Email_service


class Auth_service:
    db = App_ORM()
    Lock = threading.Lock()
    pepper = os.environ.get("PEPPER")
    if not pepper:
        raise ValueError("PEPPER env variable not set!")

    @staticmethod
    def hash_password(password: str, salt: bytes):
        return hashlib.sha256(password.encode() + salt + Auth_service.pepper.encode()).hexdigest()

    @staticmethod
    def create_user(email, password):
        salt = os.urandom(32)
        h_pass = Auth_service.hash_password(password, salt)
        return User(None, email, h_pass, salt)

    @staticmethod
    def create_verification_code():
        return f"{random.randint(10000, 100000)}"

    @staticmethod
    def send_verification_code(email, method: str, code):
        Email_service.send_email(email,
                                 f"{method} verification code",
                                 f"""Your two-factor {method.lower()} code
Code: {code}
Use this code to complete your {method.lower()}.""")

    @staticmethod
    def login(email, password):
        with Auth_service.Lock:
            if not Auth_service.db.user_exists(email):
                raise Exception("user doesn't exist")

        with Auth_service.Lock:
            user = Auth_service.db.get_user_by_email(email)
        if user == Auth_service.create_user(email, password):
            return user

    @staticmethod
    def signup(email, password):
        with Auth_service.Lock:
            if Auth_service.db.user_exists(email):
                raise Exception("user exists")

        user = Auth_service.create_user(email, password)
        with Auth_service.Lock:
            Auth_service.db.insert_user(user)
        return user

    @staticmethod
    def verify(user, method):
        code = Auth_service.create_verification_code()
        with Auth_service.Lock:
            Auth_service.db.insert_verification_info(Verification_info(user.user_id, code))
        Auth_service.send_verification_code(user.email, method, code)
