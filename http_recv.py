__author__ = "Guy Mosseri"

import socket

def recv_http(c):
    data = b""
    while True:
        try:
            data += c.recv(2 ** 16)
            if data == b"":
                return {"status": False}
            elif b"\r\n\r\n" in data:
                status = True
                headers, data = data.split(b"\r\n\r\n")
                msg_code, path, version = headers.decode().split("\r\n")[0].split(" ")
                headers = headers.decode().split("\r\n")[1:]
                headers_pairs = {}
                for header in headers:
                    k, v = header.split(": ")
                    headers_pairs[k.lower()] = v
                if "content-length" in headers_pairs.keys():
                    while len(data) < int(headers_pairs["content-length"]):
                        data += c.recv(2 ** 16)
                        if data == b"":
                            status = False
                            break
                return {"status": status,"method": msg_code, "url":path.replace("/", "\\"),"version":version,"headers":headers_pairs,"body":data }
        except ConnectionAbortedError as e:
            print(e)
            return {"status": False}

def main():
    s = socket.socket()
    s.bind(("0.0.0.0", 80))
    s.listen(3)
    while True:
        c, a = s.accept()
        x = recv_http(c)
        print(x)



if __name__ == "__main__":
    main()