__author__ = "Guy Mosseri"

import socket
import threading
from services.http_service import Http_service
from router import Router


def handle_client(client: socket.socket, addr):
    while True:
        msg = Http_service.recv_http(client)
        print(f"Received msg from: {addr}\n{msg}")
        if not msg["status"]:
            client.close()
            break

        Router.route_request(client, msg)


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
