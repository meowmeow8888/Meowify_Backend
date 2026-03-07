__author__ = "Guy Mosseri"

import socket
import threading
import os
from http_recv import recv_http
from SQL_ORM import *
from msg_handler import Msg_handler

Lock = threading.Lock()
db = App_ORM()
pepper = os.environ.get("PEPPER")
if not pepper:
    raise ValueError("PEPPER env variable not set!")

def handle_client(client: socket.socket, addr):
    while True:
        msg = recv_http(client)
        print(f"Received msg from: {addr}\n{msg}")
        if not msg["status"]:
            client.close()
            break
        url = msg["url"].split("\\")[-1]
        if url == "login":
            Msg_handler.handle_login(client, msg)
        elif url == "signup":
            Msg_handler.handle_signup(client, msg)




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
