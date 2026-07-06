import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

ADS_ENABLED_PROPERTIES = {
    "193",
    "45",
}


class DriivzAdHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json") -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self) -> None:
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        property_id = query.get("property", [None])[0]

        # Sert les images dans le dossier Assets
        if path.startswith("/Assets/"):
            file_path = "." + path

            if not os.path.exists(file_path):
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Image not found"}).encode())
                return

            self._set_headers(200, "image/png")

            with open(file_path, "rb") as file:
                self.wfile.write(file.read())
            return

        if path == "/ads/check":
            if property_id is None:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'property' parameter"}).encode())
                return

            has_ads = 1 if property_id in ADS_ENABLED_PROPERTIES else 0

            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"ads": has_ads}).encode())
            return

        if path == "/ads/content":
            html_content = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>
html, body {
    margin: 0;
    padding: 0;
    background: #ffffff;
}

img {
    width: 100%;
    height: 100vh;
    object-fit: cover;
    display: block;
}
</style>
</head>

<body>
<img src="/Assets/promo.png" alt="Promotion Couche-Tard">
</body>
</html>
            """

            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write(html_content.encode("utf-8"))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Not found"}).encode())


def run_server(server_class=HTTPServer, handler_class=DriivzAdHandler) -> None:
    port = int(os.getenv("PORT", "8000"))
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Serving on port {port}…")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run_server()