__author__ = "Guy Mosseri"

import re
from handlers.auth_handler import Auth_handler
from handlers.home_handler import Home_handler
from services.http_service import HttpResponse, HttpRequest


class Router:
    ROUTES = [
        ("POST", r"^/login$", Auth_handler.login),
        ("POST", r"^/signup$", Auth_handler.signup),
        ("POST", r"^/verify$", Auth_handler.verify),
        ("GET", r"^/$", Home_handler.Home),
        ("GET", r"^/me$", Auth_handler.me)
    ]

    @staticmethod
    def route_request(client, req: HttpRequest):
        path = req.path
        method = req.method

        if method == "OPTIONS":
            res = HttpResponse.ok()
            res.add_header("Access-Control-Allow-Headers", "Content-Type")
            res.add_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            client.send(res.to_bytes())
            return

        for route_method, pattern, handler in Router.ROUTES:
            if route_method == method:
                match = re.match(pattern, path)
                if match:
                    params = match.groups()
                    handler(client, req, *params)
                    return

        res = HttpResponse.not_found().to_bytes()
        client.send(res)
