import os
import hashlib
import socket
import json
import random

from email_handler import Email_handler
from server import db, Lock, pepper
from SQL_ORM import User, Verification_info


class Msg_handler:
    @staticmethod
    def hash_password(password: str, salt: bytes):
        return hashlib.sha256(password.encode() + salt + pepper.encode()).hexdigest()

    @staticmethod
    def create_user(email, password):
        salt = os.urandom(32)
        h_pass = Msg_handler.hash_password(password, salt)
        return User(None, email, h_pass, salt)

    @staticmethod
    def build_response(version, code, method, headers, body=b""):
        seperator = "\r\n"
        headers = seperator.join(headers)
        return f"{version} {code} {method}{seperator}{headers}{seperator + seperator}".encode() + body

    @staticmethod
    def create_verification_code():
        return f"{random.randint(10000, 100000)}"

    @staticmethod
    def handle_login(client: socket.socket, msg: dict):
        body = msg["body"].decode()
        email, password = json.loads(body).values()
        with Lock:
            user = db.get_user_by_email(email)
        if not user:
            client.send(Msg_handler.build_response(msg["version"], "401", "Unauthorized",
                                                   {"Content-Type": "application/json", "Cache-Control": "no-store"}))
            pass  # respond with an error that the user doesn't exist
        else:  # hash pass and check if creds are correct
            pass  # respond with OK 200 and give session cookie or smth + send verify code to the email

    @staticmethod
    def handle_signup(client: socket.socket, msg: dict):
        body = msg["body"].decode()
        email, password = json.loads(body).values()
        with Lock:
            user = db.get_user_by_email(email)
        if not user:
            user = Msg_handler.create_user(email, password)
            code = Msg_handler.create_verification_code()

            # inserts to db
            db.insert_user(user)
            db.insert_verification_info(Verification_info(user.user_id, code))

            # send staff
            Email_handler.send_verification_code(user.email, "Sign Up", code)
            client.send(Msg_handler.build_response(msg["version"], "200", "Ok", {}))
        else:
            client.send(Msg_handler.build_response(msg["version"], "401", "Unauthorized",
                                                   {"Content-Type": "application/json", "Cache-Control": "no-store"}))
