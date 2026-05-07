from base64 import b64encode
from hashlib import sha1
import socket
import json

from services.http_service import HttpRequest, HttpResponse


class wsMsg:
    OP_CONT = 0
    OP_TEXT = 1
    OP_BINARY = 2
    OP_CLOSE = 8
    OP_PING = 9
    OP_PONG = 10

    MAX_PAYLOAD = 2 ** 20

    def __init__(self, fin, opcode, payload):
        if len(payload) > self.MAX_PAYLOAD:
            raise OverflowError("payload cannot be longer than 1 MB")
        self.fin = fin
        self.opcode = opcode
        self.payload = payload

    def __add__(self, other):
        if not isinstance(other, wsMsg):
            return NotImplemented

        if type(self.payload) == type(other.payload):
            return wsMsg(self.fin, self.opcode, self.payload + other.payload)
        if type(self.payload) == bytes:
            return wsMsg(self.fin, self.opcode, self.payload + other.payload.encode())
        return wsMsg(self.fin, self.opcode, self.payload.encode() + other.payload)

    @staticmethod
    def ping():
        return wsMsg(1, wsMsg.OP_PING, "")

    @staticmethod
    def pong():
        return wsMsg(1, wsMsg.OP_PONG, "")

    @staticmethod
    def close(payload):
        return wsMsg(1, wsMsg.OP_CLOSE, payload)

    @staticmethod
    def text(payload):
        return wsMsg(1, wsMsg.OP_TEXT, payload)

    @staticmethod
    def binary(payload):
        return wsMsg(1, wsMsg.OP_BINARY, payload)

    @staticmethod
    def continuation(payload):
        return wsMsg(1, wsMsg.OP_CONT, payload)

    def to_bytes(self):
        frame = bytearray()

        frame.append((self.fin << 7) | self.opcode)
        payload = self.payload if type(self.payload) == bytes else self.payload.encode()

        payload_len = len(payload)
        if payload_len <= 125:
            frame.append(payload_len)
        elif payload_len <= 65535:
            frame.append(126)
            frame.extend(payload_len.to_bytes(2, "big"))
        else:
            frame.append(127)
            frame.extend(payload_len.to_bytes(8, "big"))

        frame.extend(payload)
        return bytes(frame)


class websocket:
    def __init__(self, client: socket.socket):
        self.client = client

    def handshake(self, upgrade_req: HttpRequest):
        guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        key = upgrade_req.headers.get("sec-websocket-key")
        res_key = b64encode(sha1((key.strip() + guid).encode()).digest()).decode()
        res = HttpResponse.upgrade(res_key).to_bytes()
        self.client.send(res)

    def send(self, msg: wsMsg):
        self.client.send(msg.to_bytes())

    def recv_exact(self, n):
        data = b""
        while len(data) < n:
            chunk = self.client.recv(n - len(data))
            if not chunk:
                raise ConnectionError("socket closed")
            data += chunk
        return data

    def recv(self) -> wsMsg:
        fin = 0
        msgs = []
        size = 0
        while not fin:
            first_byte = self.recv_exact(1)[0]
            second_byte = self.recv_exact(1)[0]

            fin = (first_byte >> 7) & 1
            rsv_bytes = first_byte & 0b01110000
            opcode = first_byte & 0b00001111

            if opcode == wsMsg.OP_PING:
                self.send(wsMsg.pong())
                fin = 0
                continue
            elif opcode == wsMsg.OP_PONG:
                fin = 0
                continue

            if rsv_bytes:
                self.client.close()
                raise ConnectionError("ws connection error (rsv)")

            masked = second_byte >> 7
            payload_len = second_byte & 0x7F

            if payload_len == 126:
                payload_len = int.from_bytes(self.recv_exact(2), "big")
            elif payload_len == 127:
                payload_len = int.from_bytes(self.recv_exact(8), "big")

            size += payload_len
            if wsMsg.MAX_PAYLOAD < size:
                raise OverflowError("payload cannot be longer than 1 MB")

            if not masked:
                raise ValueError("Client frames must be masked")
            mask = self.recv_exact(4)
            payload = bytearray(self.recv_exact(payload_len))

            for i in range(len(payload)):
                payload[i] ^= mask[i % 4]
            if not msgs:
                if opcode == 1:
                    msgs.append(wsMsg.text(payload))
                elif opcode == 2:
                    msgs.append(wsMsg.binary(payload))
                elif opcode == 8:
                    self.send(wsMsg.close("connection failed"))
                    self.client.close()
                    return
                else:
                    raise ValueError("Unexpected opcode")
            else:
                if opcode == 0:
                    msgs.append(wsMsg.continuation(payload))
                else:
                    raise ValueError("Unexpected opcode")

        msg = msgs[0]
        t = type(msg.payload)
        for m in msgs[1:]:
            if t != type(m.payload):
                raise ValueError("different fragment types")
            msg += m
        if msg.opcode == wsMsg.OP_TEXT:
            msg.payload = json.loads(msg.payload.decode())
        return msg
