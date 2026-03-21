import socket

from services.http_service import HttpRequest
from websocket import websocket


class Home_handler:
    @staticmethod
    def Home(client: socket.socket, req: HttpRequest):
        if req.headers.get("Connection", None) != "Upgrade":
            return
        if req.headers.get("Upgrade", None) != "websocket":
            return

        ws = websocket()
        res = ws.handshake(req)
        client.send(res)
        # idk add a loop maybe ill think about u tomorrow