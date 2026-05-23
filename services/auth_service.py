import os
import hashlib
import random
import threading
from datetime import datetime, timedelta

from SQL_ORM import User, App_ORM, Verification_info
from services.email_service import Email_service


class Auth_service:
    db = App_ORM()
    Lock = threading.Lock()
    pepper = os.environ.get("PEPPER")
    if not pepper:
        raise ValueError("PEPPER env variable not set!")
    SESSION_TIMEOUT_DAYS = 7
    VERIFICATION_CODE_TIMEOUT = 2

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
        return f"{random.randint(100000, 1000000)}"

    @staticmethod
    def send_verification_code(email, code):
        Email_service.send_email(email,
                                 f"Login verification code",
                                 f"""Your two-factor login code
Code: {code}
Use this code to complete your login.""")

    @staticmethod
    def is_session_valid(session):
        last_seen = datetime.fromisoformat(str(session.created_at))
        return datetime.now() - last_seen < timedelta(days=Auth_service.SESSION_TIMEOUT_DAYS)

    @staticmethod
    def login(email, password):
        with Auth_service.Lock:
            if not Auth_service.db.user_exists(email):
                raise Exception("user doesn't exist")

        with Auth_service.Lock:
            user = Auth_service.db.get_user_by_email(email)

        h_pass = Auth_service.hash_password(password, user.salt)
        if h_pass != user.password:
            raise Exception("user credentials are wrong")
        return user

    @staticmethod
    def signup(email, password):
        with Auth_service.Lock:
            if Auth_service.db.user_exists(email):
                raise Exception("user exists")

        user = Auth_service.create_user(email, password)
        with Auth_service.Lock:
            Auth_service.db.insert_user(user)

    @staticmethod
    def send_verify(user):
        Auth_service.db.del_verification_info_by_user_id(user.user_id)
        code = Auth_service.create_verification_code()
        print("sent code - " + code)
        with Auth_service.Lock:
            Auth_service.db.insert_verification_info(Verification_info(user.user_id, code))
        Auth_service.send_verification_code(user.email, code)

    @staticmethod
    def verify(user, passcode):
        with Auth_service.Lock:
            verf_info = Auth_service.db.get_verification_info_by_user_id(user.user_id)
        if not verf_info:
            raise Exception("no code for this user")
        print(verf_info.code, passcode)
        if verf_info.code != passcode:
            raise Exception("incorrect passcode")
        sent_at = datetime.fromisoformat(str(verf_info.time))
        if datetime.now() - sent_at > timedelta(minutes=Auth_service.VERIFICATION_CODE_TIMEOUT):
            raise Exception("max time has passed already")
