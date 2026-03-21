__author__ = "Guy Mosseri"


class Http_service:
    @staticmethod
    def recv_http(c):
        data = b""
        while True:
            try:
                chunk = c.recv(2 ** 16)
                if not chunk:
                    return {"status": False}
                data += chunk

                if b"\r\n\r\n" in data:
                    headers, data = data.split(b"\r\n\r\n", 1)
                    method, path, version = headers.decode().split("\r\n")[0].split(" ")
                    headers = headers.decode().split("\r\n")[1:]
                    headers_pairs = {}

                    for header in headers:
                        k, v = header.split(": ", 1)
                        headers_pairs[k.lower()] = v

                    if "content-length" in headers_pairs.keys():
                        content_length = int(headers_pairs["content-length"])
                        if content_length > 10 * 1024 * 1024:
                            return None

                        while len(data) < content_length:
                            data += c.recv(2 ** 16)
                            if data == b"":
                                break

                    return HttpRequest(method, path, version, headers_pairs, data)

            except ConnectionAbortedError:
                return None

    @staticmethod
    def build_response(version, code, method, headers, body=b""):
        seperator = "\r\n"
        headers = seperator.join(f"{k}: {v}" for k, v in headers.items())
        return f"{version} {code} {method}{seperator}{headers}{seperator + seperator}".encode() + body


class HttpResponse:
    def __init__(self, version, status_code, reason_phrase, headers, body=b""):
        self.version = version
        self.status_code = status_code
        self.reason_phrase = reason_phrase
        self.headers = headers
        self.body = body

    def to_bytes(self):
        seperator = "\r\n"
        headers = seperator.join(f"{k}: {v}" for k, v in self.headers.items())
        return f"{self.version} {self.status_code} {self.reason_phrase}{seperator}{headers}{seperator}{seperator}".encode() + self.body

    @staticmethod
    def not_found():
        return HttpResponse("HTTP/1.1", "404", "Not Found", {"Content-Type": "text/plain", "Content-Length": "15"},
                            b"Route not found")

    @staticmethod
    def ok():
        return HttpResponse("HTTP/1.1", "200", "Ok", {"Content-Length": "0"})

    @staticmethod
    def unauthorized(error):
        return HttpResponse("HTTP/1.1", "401", "Unauthorized",
                            {"Content-Type": "text/plain", "Content-Length": f"{len(error)}"}, f"{error}".encode())


class HttpRequest:
    def __init__(self, method, path, version, headers, body=b""):
        self.method = method
        self.path = path
        self.version = version
        self.headers = headers
        self.body = body

    def __repr__(self):
        return f"Request - {self.method}\nto: {self.path}\nheaders: {"\n".join(self.headers)}\nbody: {self.body}"
