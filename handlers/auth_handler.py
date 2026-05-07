import socket
import json
import secrets

from services.auth_service import Auth_service
from services.http_service import HttpResponse, HttpRequest


class Auth_handler:
    @staticmethod
    def login(client: socket.socket, req: HttpRequest):
        print("handling login...")
        body = json.loads(req.body.decode())
        email = body["email"]
        password = body["password"]

        try:
            user = Auth_service.login(email, password)
            print("found user")

            res = HttpResponse.ok()
            client.send(res.to_bytes())

            Auth_service.send_verify(user)

        except Exception as e:
            print(e)
            client.send(HttpResponse.unauthorized(str(e)).to_bytes())

    @staticmethod
    def signup(client: socket.socket, req: HttpRequest):
        print("handling signup...")
        body = json.loads(req.body.decode())
        email = body["email"]
        password = body["password"]
        try:
            Auth_service.signup(email, password)
            print("created user successfully")
            client.send(HttpResponse.ok().to_bytes())
        except Exception as e:
            print(e)
            client.send(HttpResponse.unauthorized(str(e)).to_bytes())

    @staticmethod
    def me(client: socket.socket, req: HttpRequest):
        print("handling me...")
        try:
            cookies = req.headers.get("cookie", "")

            session_id = None
            for part in cookies.split(";"):
                part = part.strip()
                if part.startswith("session="):
                    session_id = part.split("=", 1)[1]

            if not session_id:
                print("no session received")
                client.send(HttpResponse.unauthorized("no session").to_bytes())
                return
            with Auth_service.Lock:
                session = Auth_service.db.get_session(session_id)
            if not session or not Auth_service.is_session_valid(session):
                print("invalid session or none at database")
                client.send(HttpResponse.unauthorized("invalid session").to_bytes())
                return

            res = HttpResponse.ok()
            res.add_header("Content-Type", "application/json")
            print("/me succeed")
            client.send(res.to_bytes())

        except Exception as e:
            print(e)
            client.send(HttpResponse.unauthorized(str(e)).to_bytes())

    @staticmethod
    def verify(client: socket.socket, req: HttpRequest):
        print("handling verify...")
        body = json.loads(req.body.decode())
        email = body["email"]
        passcode = body["passcode"]

        try:
            with Auth_service.Lock:
                user = Auth_service.db.get_user_by_email(email)

            Auth_service.verify(user, passcode)

            session_id = secrets.token_hex(32)
            with Auth_service.Lock:
                Auth_service.db.insert_session(session_id, user.user_id)

            res = HttpResponse.ok()
            res.add_header(
                "Set-Cookie",
                f"session={session_id}; HttpOnly; Path=/; SameSite=None; Secure" #"SameSite=Lax
            )
            client.send(res.to_bytes())
        except Exception as e:
            print(e)
            client.send(HttpResponse.unauthorized(str(e)).to_bytes())
