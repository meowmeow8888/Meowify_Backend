__author__ = "Guy Mosseri"

import socket
# import ssl
import threading
from services.http_service import Http_service, HttpRequest
from router import Router


def handle_client(client: socket.socket, addr):
    while True:
        req: HttpRequest = Http_service.recv_http(client)
        print(f"Received msg from: {addr}\n{req}")
        if not req:
            client.close()
            break

        Router.route_request(client, req)


def main():
    s = socket.socket()
    s.bind(("0.0.0.0", 8080))
    s.listen(5)

    # context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    while True:
        client, addr = s.accept()
        print(f"Client Connected: {addr}")
        # secure_socket = context.wrap_socket(client, server_side=True)
        threading.Thread(target=handle_client, args=(client, addr,)).start()


if __name__ == '__main__':
    main()
