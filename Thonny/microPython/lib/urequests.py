import usocket

class Response:
    def __init__(self):
        self._cached = None

    def close(self):
        if self.raw:
            self.raw.close()
            self.raw = None

    @property
    def content(self):
        if self._cached is None:
            self._cached = self.raw.read()
            self.raw.close()
            self.raw = None
        return self._cached

    @property
    def text(self):
        return str(self.content, "utf-8")

    def json(self):
        import ujson
        return ujson.loads(self.content)


def request(method, url, data=None, json=None, headers={}, stream=None):
    def parse_url(url):
        proto, _, host, path = url.split("/", 3)
        if proto == "http:":
            port = 80
        elif proto == "https:":
            import ussl
            port = 443
        else:
            raise ValueError("Unsupported protocol: " + proto[:-1])
        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)
        return proto, host, port, "/" + path

    proto, host, port, path = parse_url(url)

    if proto == "https:":
        import ussl

    ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
    ai = ai[0]
    s = usocket.socket(ai[0], ai[1], ai[2])
    try:
        s.connect(ai[-1])
        if proto == "https:":
            s = ussl.wrap_socket(s, server_hostname=host)
        s.write(b"%s %s HTTP/1.0\r\n" % (method, path))
        s.write(b"Host: %s\r\n" % host)
        if json is not None:
            assert data is None
            import ujson
            data = ujson.dumps(json)
            s.write(b"Content-Type: application/json\r\n")
        if data:
            s.write(b"Content-Length: %d\r\n" % len(data))
        for k, v in headers.items():
            s.write(b"%s: %s\r\n" % (k, v))
        s.write(b"\r\n")
        if data:
            s.write(data)

        l = s.readline()
        protover, status, msg = l.split(None, 2)
        status = int(status)
        reason = msg.rstrip()

        while True:
            l = s.readline()
            if not l or l == b"\r\n":
                break
            if l.startswith(b"Transfer-Encoding:") and b"chunked" in l:
                raise ValueError("Unsupported Transfer-Encoding")
            if l.startswith(b"Location:"):
                raise NotImplementedError("Redirects not yet supported")

        resp = Response()
        resp.status_code = status
        resp.reason = reason
        resp.raw = s
        s = None
        return resp
    finally:
        if s:
            s.close()


def head(url, **kw):
    return request("HEAD", url, **kw)


def get(url, **kw):
    return request("GET", url, **kw)


def post(url, **kw):
    return request("POST", url, **kw)


def put(url, **kw):
    return request("PUT", url, **kw)


def patch(url, **kw):
    return request("PATCH", url, **kw)


def delete(url, **kw):
    return request("DELETE", url, **kw)
