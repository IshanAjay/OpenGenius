import http.client
import time
from urllib.parse import urlparse, parse_qs, unquote, quote
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class CORSProxyHandler(BaseHTTPRequestHandler):
    MAX_REDIRECTS = 5

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        self.proxy()

    def do_POST(self):
        self.proxy()

    def proxy(self):
        start_time = time.time()
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)
        target_url = query.get("url", [None])[0]

        if not target_url:
            self.send_error(400, "Missing 'url' query parameter")
            return

        # Decode and re-encode the URL to ensure all characters are valid
        target_url = unquote(target_url)
        encoded_target_url = quote(target_url, safe=":/?&=")

        print(f"\n[{time.strftime('%X')}] {self.command} from {self.client_address[0]} → {encoded_target_url}")

        # Read the request body (for POST requests)
        content_length = int(self.headers.get("Content-Length", 0))
        request_body = self.rfile.read(content_length) if content_length else None

        # Simulate a real browser with proper headers
        headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
        headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
        headers["Accept-Encoding"] = "gzip, deflate, br"
        headers["Connection"] = "keep-alive"

        # Forward cookies
        cookies = self.headers.get('Cookie')
        if cookies:
            headers['Cookie'] = cookies

        for redirect_count in range(self.MAX_REDIRECTS):
            parsed_target = urlparse(encoded_target_url)
            scheme = parsed_target.scheme
            host = parsed_target.netloc
            path = parsed_target.path or "/"
            if parsed_target.query:
                path += "?" + parsed_target.query

            connection_class = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
            try:
                conn = connection_class(host, timeout=10)
                conn.request(self.command, path, request_body, headers)
                resp = conn.getresponse()
                data = resp.read()
                duration = time.time() - start_time

                if resp.status in (301, 302, 303, 307, 308):
                    location = resp.getheader("Location")
                    if not location:
                        break
                    target_url = location if location.startswith("http") else f"{scheme}://{host}{location}"
                    continue

                # Send response back to client
                self.send_response(resp.status, resp.reason)
                for header, value in resp.getheaders():
                    name = header.lower()
                    if name not in ("transfer-encoding", "content-length"):
                        self.send_header(header, value)

                # Always set CORS headers
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()

                self.wfile.write(data)
                self.wfile.flush()

                return

            except Exception as e:
                print(f"[!] Proxy error: {e}")
                self.send_error(502, f"Proxy error: {e}")
                return

        print("[x] Too many redirects")
        self.send_error(508, "Too many redirects")


def run_server(port=8080):
    server = ThreadingHTTPServer(("", port), CORSProxyHandler)
    print(f"🚀 CORS Proxy running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    run_server()
