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
                    status = True
                    headers, data = data.split(b"\r\n\r\n", 1)
                    msg_code, path, version = headers.decode().split("\r\n")[0].split(" ")
                    headers = headers.decode().split("\r\n")[1:]
                    headers_pairs = {}

                    for header in headers:
                        k, v = header.split(": ", 1)
                        headers_pairs[k.lower()] = v

                    if "content-length" in headers_pairs.keys():
                        content_length = int(headers_pairs["content-length"])
                        if content_length > 10 * 1024 * 1024:
                            return {"status": False}

                        while len(data) < content_length:
                            data += c.recv(2 ** 16)
                            if data == b"":
                                status = False
                                break

                    return {
                        "status": status,
                        "method": msg_code,
                        "url": path,
                        "version": version,
                        "headers": headers_pairs,
                        "body": data
                    }

            except ConnectionAbortedError:
                return {"status": False}

    @staticmethod
    def build_response(version, code, method, headers, body=b""):
        seperator = "\r\n"
        headers = seperator.join(f"{k}: {v}" for k, v in headers.items())
        return f"{version} {code} {method}{seperator}{headers}{seperator + seperator}".encode() + body
