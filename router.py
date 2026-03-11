__author__ = "Guy Mosseri"

import re
from handlers.auth_handler import Auth_handler
from services.http_service import Http_service


class Router:
    ROUTES = {
        ("POST", r"^/login$"): Auth_handler.login,
        ("POST", r"^/signup$"): Auth_handler.signup,
    }

    @staticmethod
    def route_request(client, msg):
        path = msg["url"]
        method = msg["method"]

        for route_method, pattern, handler in Router.ROUTES:
            if route_method == method:
                match = re.match(pattern, path)
                if match:
                    params = match.groups()
                    handler(client, msg, *params)
                    return

        client.send(Http_service.build_response(
            msg["version"],
            "404",
            "Not Found",
            {"Content-Type": "text/plain"},
            b"Route not found"
        )
        )
