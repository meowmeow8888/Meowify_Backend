__author__ = "Guy Mosseri"

import re
from handlers.auth_handler import Auth_handler
from handlers.home_handler import Home_handler
from services.http_service import HttpResponse, HttpRequest


class Router:
    ROUTES = {
        ("POST", r"^/login$"): Auth_handler.login,
        ("POST", r"^/signup$"): Auth_handler.signup,
        ("GET", r"^/home$"): Home_handler.Home,
    }

    @staticmethod
    def route_request(client, req: HttpRequest):
        path = req.path
        method = req.method

        for route_method, pattern, handler in Router.ROUTES:
            if route_method == method:
                match = re.match(pattern, path)
                if match:
                    params = match.groups()
                    handler(client, req, *params)
                    return

        res = HttpResponse.not_found().to_bytes()
        client.send(f"{res}")
