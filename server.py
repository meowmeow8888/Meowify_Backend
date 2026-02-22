__author__ = "Guy Mosseri"

import socket
import json
import threading
import hashlib
import os

from http_recv import recv_http
from SQL_ORM import *

Lock = threading.Lock()
db = App_ORM()
pepper = os.environ.get("PEPPER")
if not pepper:
    raise ValueError("PEPPER env variable not set!")


def hash_password(password: str, salt: bytes):
    return hashlib.sha256(password.encode() + salt + pepper.encode()).hexdigest()


def build_response(version, code, method, headers, body=b""):
    seperator = "\r\n"
    headers = seperator.join(headers)
    return f"{version} {code} {method}{seperator}{headers}{seperator + seperator}".encode() + body


def handle_client(client: socket.socket, addr):
    while True:
        msg = recv_http(client)
        print(f"Received msg from: {addr}\n{msg}")
        if not msg["status"]:
            client.close()
            break
        if msg["url"].split("\\")[-1] == "login":
            body = msg["body"].decode()
            email, password = json.loads(body).values()
            with Lock:
                user = db.get_users_by_email(email)
            if not user:
                client.send(build_response(msg["version"], "401", "Unauthorized",
                                           {"Content-Type": "application/json", "Cache-Control": "no-store"}, ))
                pass  # respond with an error that the user doesn't exist
            else: # hash pass and check if creds are correct
                pass  # respond with OK 200 and give session cookie or smth + send verify code to the email


def main():
    s = socket.socket()
    s.bind(("0.0.0.0", 8080))
    s.listen(3)
    while True:
        client, addr = s.accept()
        print(f"Client Connected: {addr}")
        threading.Thread(target=handle_client, args=(client, addr,)).start()


if __name__ == '__main__':
    main()
