import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote


# ==========================================================
# CONFIGURATION
# ==========================================================

ADS_BY_PROPERTY = {
    "193": "Car-wash.png"
}


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "Assets")


class DriivzAdHandler(BaseHTTPRequestHandler):

    def send_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.end_headers()


    # ======================================================
    # RENDER HEALTH CHECK
    # ======================================================

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()


    # ======================================================
    # GET
    # ======================================================

    def do_GET(self):

        parsed = urlparse(self.path)

        path = unquote(parsed.path)
        query = parse_qs(parsed.query)

        property_id = query.get("property", [None])[0]
        country = query.get("country", [None])[0]


        # ==================================================
        # HOME
        # ==================================================

        if path == "/":

            self.send_headers(
                200,
                "text/plain; charset=utf-8"
            )

            message = (
                "Driivz Ads Server OK\n"
                f"BASE_DIR: {BASE_DIR}\n"
                f"ASSETS_DIR: {ASSETS_DIR}\n"
                f"Assets exists: {os.path.isdir(ASSETS_DIR)}\n"
            )

            if os.path.isdir(ASSETS_DIR):
                message += f"Assets: {os.listdir(ASSETS_DIR)}\n"

            self.wfile.write(
                message.encode("utf-8")
            )

            return


        # ==================================================
        # ASSETS
        # ==================================================

        if path.startswith("/Assets/"):

            filename = path[len("/Assets/"):]

            file_path = os.path.join(
                ASSETS_DIR,
                filename
            )

            print(
                f"ASSET REQUEST: {filename}",
                flush=True
            )

            print(
                f"FULL PATH: {file_path}",
                flush=True
            )

            print(
                f"EXISTS: {os.path.isfile(file_path)}",
                flush=True
            )

            if os.path.isdir(ASSETS_DIR):

                print(
                    f"FILES: {os.listdir(ASSETS_DIR)}",
                    flush=True
                )

            else:

                print(
                    "ASSETS DIRECTORY DOES NOT EXIST",
                    flush=True
                )


            if not os.path.isfile(file_path):

                self.send_headers(
                    404,
                    "application/json"
                )

                response = {
                    "error": "Image not found",
                    "requested_file": filename,
                    "assets_directory": ASSETS_DIR,
                    "assets_directory_exists":
                        os.path.isdir(ASSETS_DIR),
                    "available_files":
                        os.listdir(ASSETS_DIR)
                        if os.path.isdir(ASSETS_DIR)
                        else []
                }

                self.wfile.write(
                    json.dumps(
                        response,
                        indent=2
                    ).encode("utf-8")
                )

                return


            extension = os.path.splitext(
                filename
            )[1].lower()


            content_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
                ".gif": "image/gif",
            }


            content_type = content_types.get(
                extension,
                "application/octet-stream"
            )


            self.send_headers(
                200,
                content_type
            )


            with open(file_path, "rb") as f:
                self.wfile.write(f.read())

            return


        # ==================================================
        # DRIIVZ CHECK
        # ==================================================

        if path == "/ads/check":

            if property_id is None:

                self.send_headers(400)

                self.wfile.write(
                    json.dumps({
                        "error": "Missing property"
                    }).encode()
                )

                return


            ads = (
                1
                if property_id in ADS_BY_PROPERTY
                else 0
            )


            self.send_headers(200)


            self.wfile.write(
                json.dumps({
                    "ads": ads
                }).encode()
            )

            return


        # ==================================================
        # DRIIVZ CONTENT
        # ==================================================

        if path == "/ads/content":

            if property_id is None:

                self.send_headers(400)

                self.wfile.write(
                    json.dumps({
                        "error": "Missing property"
                    }).encode()
                )

                return


            image = ADS_BY_PROPERTY.get(
                property_id
            )


            if image is None:

                self.send_headers(404)

                self.wfile.write(
                    json.dumps({
                        "error":
                        "No ad configured for property"
                    }).encode()
                )

                return


            html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<style>

html,
body {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
}}

img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}}

</style>

</head>

<body>

<img src="/Assets/{image}">

</body>

</html>
"""


            self.send_headers(
                200,
                "text/html; charset=utf-8"
            )


            self.wfile.write(
                html.encode("utf-8")
            )

            return


        # ==================================================
        # 404
        # ==================================================

        self.send_headers(404)

        self.wfile.write(
            json.dumps({
                "error": "Not found"
            }).encode()
        )


# ==========================================================
# SERVER
# ==========================================================

def run_server():

    port = int(
        os.getenv(
            "PORT",
            "8000"
        )
    )


    print(
        f"BASE_DIR = {BASE_DIR}",
        flush=True
    )

    print(
        f"ASSETS_DIR = {ASSETS_DIR}",
        flush=True
    )

    print(
        f"ASSETS EXISTS = {os.path.isdir(ASSETS_DIR)}",
        flush=True
    )


    if os.path.isdir(ASSETS_DIR):

        print(
            f"ASSETS FILES = {os.listdir(ASSETS_DIR)}",
            flush=True
        )


    server = HTTPServer(
        ("", port),
        DriivzAdHandler
    )


    print(
        f"Serving on port {port}",
        flush=True
    )


    server.serve_forever()


if __name__ == "__main__":
    run_server()
