import socket
import json

from services.auth_service import Auth_service
from services.http_service import Http_service


class Auth_handler:
    @staticmethod
    def login(client: socket.socket, msg: dict):
        body = msg["body"].decode()
        email, password = json.loads(body).values()
        try:
            user = Auth_service.login(email, password)
            client.send(Http_service.build_response(msg["version"], "200", "Ok", {}))
            Auth_service.verify(user, "Login")
        except Exception as e:
            client.send(Http_service.build_response(msg["version"], "401", "Unauthorized",
                                                    {"Content-Type": "application/json", "Cache-Control": "no-store"},
                                                    f"{e}".encode()))

    @staticmethod
    def signup(client: socket.socket, msg: dict):
        body = msg["body"].decode()
        email, password = json.loads(body).values()
        try:
            user = Auth_service.signup(email, password)
            client.send(Http_service.build_response(msg["version"], "200", "Ok", {}))
            Auth_service.verify(user, "Sign up")
        except Exception as e:
            client.send(Http_service.build_response(msg["version"], "401", "Unauthorized",
                                                    {"Content-Type": "application/json", "Cache-Control": "no-store"},
                                                    f"{e}".encode()))
