import socket
import json

from services.auth_service import Auth_service
from services.http_service import HttpResponse, HttpRequest


class Auth_handler:
    @staticmethod
    def login(client: socket.socket, req: HttpRequest):
        body = req.body.decode()
        email, password = json.loads(body).values()
        try:
            user = Auth_service.login(email, password)
            client.send(HttpResponse.ok().to_bytes())
            Auth_service.verify(user, "Login")
        except Exception as e:
            client.send(HttpResponse.unauthorized(e).to_bytes())

    @staticmethod
    def signup(client: socket.socket, req: HttpRequest):
        body = req.body.decode()
        email, password = json.loads(body).values()
        try:
            user = Auth_service.signup(email, password)
            client.send(HttpResponse.ok().to_bytes())
            Auth_service.verify(user, "Sign up")
        except Exception as e:
            client.send(HttpResponse.unauthorized(e).to_bytes())
