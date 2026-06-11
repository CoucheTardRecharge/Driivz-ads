"""
Simple HTTP server for Driivz ad integration using Python's standard library.

This script avoids third‑party dependencies like Flask by subclassing
`http.server.BaseHTTPRequestHandler`. It provides two endpoints:

1. `/ads/check` – Accepts `property` and `country` query parameters and
   returns a JSON object `{ "ads": 1 }` if the property ID is in
   `ADS_ENABLED_PROPERTIES`, otherwise `{ "ads": 0 }`.

2. `/ads/content` – Accepts the same query parameters and returns
   responsive HTML content. You can customize the HTML template as
   needed for your campaign.

Usage:

```
python server.py
```

The server binds to localhost on port 8000 by default. You can change
the port by setting the `PORT` environment variable.

Test the endpoints with curl:

```
curl "http://localhost:8000/ads/check?property=486&country=CA"
curl "http://localhost:8000/ads/content?property=486&country=CA"
```
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# Define which properties have ads enabled.
ADS_ENABLED_PROPERTIES = {
    "486",
    "6001124",
    "6000930",
    "451",
    "620",
    "17",
    "1",
}


class DriivzAdHandler(BaseHTTPRequestHandler):
    """Custom HTTP request handler for Driivz ad API."""

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json") -> None:
        """Send HTTP headers."""
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        # CORS headers for local testing; remove or adjust for production
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        property_id = query.get("property", [None])[0]
        country = query.get("country", [None])[0]

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
            # Basic HTML template; customize as needed
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ad Content</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f7f7f7; }}
        .container {{ max-width: 600px; margin: 50px auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .button {{ display: inline-block; padding: 10px 20px; margin-top: 20px; background: #d71920; color: #fff; text-decoration: none; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Special Offer!</h2>
        <p>Unlock a 20% discount on your next purchase.</p>
        <p>Property: {property_id or 'N/A'}</p>
        <p>Country: {country or 'N/A'}</p>
        <a href="https://www.yourwebsite.com/offer" class="button" target="_blank">Learn More</a>
    </div>
</body>
</html>
            """
            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write(html_content.encode("utf-8"))
            return

        # Unknown path
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Not found"}).encode())


def run_server(server_class=HTTPServer, handler_class=DriivzAdHandler) -> None:
    """Run the HTTP server."""
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