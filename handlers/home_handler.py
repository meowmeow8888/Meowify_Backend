import socket
import threading
from queue import Queue

from services.http_service import HttpRequest, HttpResponse
from websocket import websocket, wsMsg
from handlers.event_handler import Event_Handler, Instruction


class Home_handler:
    @staticmethod
    def msg_parser(msg: wsMsg):
        payload = msg.payload
        if not payload:
            return
        try:
            inst = payload["inst"]
            params = payload["params"]
            return Instruction(inst, params)
        except Exception as e:
            print(e)
            return


    @staticmethod
    def Home(client: socket.socket, req: HttpRequest):
        if req.headers.get("connection", None) != "Upgrade":
            client.send(HttpResponse.not_found().to_bytes())
            return
        if req.headers.get("upgrade", None) != "websocket":
            client.send(HttpResponse.not_found().to_bytes())
            return

        print("connecting ws...")
        ws = websocket(client)
        ws.handshake(req)
        print("ws connected")

        q : Queue[Instruction] = Queue()
        threading.Thread(target=Event_Handler.event_loop, args=(ws, q,)).start()
        while True:
            try:
                msg = ws.recv()
            except Exception as e:
                print(e)
                return
            if msg.opcode == wsMsg.OP_TEXT:
                inst = Home_handler.msg_parser(msg)
                if inst:
                    q.put(inst)
