import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs


# ==========================================================
# CONFIGURATION DES PUBLICITÉS
# ==========================================================
#
# Associer chaque Property ID Driivz à son image.
#
# Les images doivent être présentes dans le dossier Assets.
#
# Exemple :
# "193": "Car Wash.png"
# "45": "promo-combo.png"
#
# Si un Property ID n'est pas dans cette liste :
# {"ads": 0}
# ==========================================================

ADS_BY_PROPERTY = {
    "193": "Car Wash.png",
    "45": "promo-combo.png",
}


class DriivzAdHandler(BaseHTTPRequestHandler):

    def _set_headers(
        self,
        status_code: int = 200,
        content_type: str = "application/json"
    ) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self) -> None:
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        property_id = query.get("property", [None])[0]
        country = query.get("country", [None])[0]

        # ==========================================================
        # IMAGES / ASSETS
        # ==========================================================

        if path.startswith("/Assets/"):
            file_path = "." + path

            if not os.path.exists(file_path):
                self._set_headers(404)
                self.wfile.write(
                    json.dumps({"error": "Image not found"}).encode()
                )
                return

            if file_path.lower().endswith(".png"):
                content_type = "image/png"
            elif file_path.lower().endswith((".jpg", ".jpeg")):
                content_type = "image/jpeg"
            elif file_path.lower().endswith(".webp"):
                content_type = "image/webp"
            else:
                content_type = "application/octet-stream"

            self._set_headers(200, content_type)

            with open(file_path, "rb") as file:
                self.wfile.write(file.read())

            return

        # ==========================================================
        # ÉTAPE 1 - DRIIVZ CHECK
        # ==========================================================
        #
        # Exemple :
        # /ads/check?property=193&country=CA
        #
        # 193 -> {"ads": 1}
        # 45  -> {"ads": 1}
        # autre -> {"ads": 0}
        # ==========================================================

        if path == "/ads/check":

            if property_id is None:
                self._set_headers(400)
                self.wfile.write(
                    json.dumps(
                        {"error": "Missing 'property' parameter"}
                    ).encode()
                )
                return

            has_ads = 1 if property_id in ADS_BY_PROPERTY else 0

            self._set_headers(200, "application/json")
            self.wfile.write(
                json.dumps({"ads": has_ads}).encode()
            )
            return

        # ==========================================================
        # ÉTAPE 2 - DRIIVZ CONTENT
        # ==========================================================
        #
        # 193 -> Car Wash.png
        # 45  -> promo-combo.png
        # ==========================================================

        if path == "/ads/content":

            if property_id is None:
                self._set_headers(400)
                self.wfile.write(
                    json.dumps(
                        {"error": "Missing 'property' parameter"}
                    ).encode()
                )
                return

            ad_image = ADS_BY_PROPERTY.get(property_id)

            if ad_image is None:
                self._set_headers(404)
                self.wfile.write(
                    json.dumps(
                        {"error": "No ad configured for this property"}
                    ).encode()
                )
                return

            html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Couche-Tard Recharge</title>

<style>
html, body {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: #ffffff;
    overflow: hidden;
}}

img {{
    width: 100%;
    height: 100vh;
    object-fit: cover;
    display: block;
}}
</style>
</head>

<body>
    <img
        src="/Assets/{ad_image}"
        alt="Promotion Couche-Tard"
    >
</body>
</html>
"""

            self._set_headers(
                200,
                "text/html; charset=utf-8"
            )
            self.wfile.write(
                html_content.encode("utf-8")
            )
            return

        # ==========================================================
        # 404
        # ==========================================================

        self._set_headers(404)
        self.wfile.write(
            json.dumps({"error": "Not found"}).encode()
        )


def run_server(
    server_class=HTTPServer,
    handler_class=DriivzAdHandler
) -> None:

    port = int(os.getenv("PORT", "8000"))
    server_address = ("", port)

    httpd = server_class(
        server_address,
        handler_class
    )

    print(f"Serving on port {port}...")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run_server()
