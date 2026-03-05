import os
import hashlib
import socket
import json
from server import db, Lock, pepper
from SQL_ORM import User


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
    def handle_login(client: socket.socket, msg: dict):
        body = msg["body"].decode()
        email, password = json.loads(body).values()
        with Lock:
            user = db.get_user_by_email(email)
        if not user:
            client.send(Msg_handler.build_response(msg["version"], "401", "Unauthorized",
                                       {"Content-Type": "application/json", "Cache-Control": "no-store"}, ))
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
            db.insert_user(user)
        else:
            print(user)
