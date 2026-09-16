import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote


# ==========================================================
# CONFIGURATION DES PUBLICITÉS
# ==========================================================
#
# Associer chaque Property ID Driivz à son image.
#
# Les images doivent être dans le dossier :
#
# Assets/
#
# Exemple :
# 193 -> Car-Wash.png
# 45  -> promo-combo.png
#
# Tous les autres Property ID recevront :
# {"ads": 0}
# ==========================================================

ADS_BY_PROPERTY = {
    "193": "Car-Wash.png",
    "45": "promo-combo.png",
}


# ==========================================================
# DOSSIERS
# ==========================================================
#
# On détermine le dossier où se trouve server.py.
# Cela évite les problèmes de Working Directory sur Render.
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "Assets")


class DriivzAdHandler(BaseHTTPRequestHandler):

    def _set_headers(
        self,
        status_code: int = 200,
        content_type: str = "application/json"
    ) -> None:

        self.send_response(status_code)

        self.send_header(
            "Content-Type",
            content_type
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Cache-Control",
            "no-cache, no-store, must-revalidate"
        )

        self.send_header(
            "Pragma",
            "no-cache"
        )

        self.send_header(
            "Expires",
            "0"
        )

        self.end_headers()


    # ======================================================
    # HEAD
    # ======================================================
    #
    # Render peut envoyer une requête HEAD pour vérifier
    # que le serveur répond.
    # ======================================================

    def do_HEAD(self) -> None:

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()


    # ======================================================
    # GET
    # ======================================================

    def do_GET(self) -> None:

        parsed_path = urlparse(self.path)

        path = unquote(parsed_path.path)

        query = parse_qs(
            parsed_path.query
        )

        property_id = query.get(
            "property",
            [None]
        )[0]

        country = query.get(
            "country",
            [None]
        )[0]


        # ==================================================
        # ASSETS / IMAGES
        # ==================================================
        #
        # Exemple :
        #
        # /Assets/Car-Wash.png
        #
        # devient :
        #
        # /.../Assets/Car-Wash.png
        #
        # ==================================================

        if path.startswith("/Assets/"):

            filename = os.path.basename(path)

            file_path = os.path.join(
                ASSETS_DIR,
                filename
            )


            # ==============================================
            # DIAGNOSTIC RENDER
            # ==============================================

            print("")
            print("========== ASSET REQUEST ==========")
            print(f"Requested URL: {path}")
            print(f"Filename: {filename}")
            print(f"BASE_DIR: {BASE_DIR}")
            print(f"ASSETS_DIR: {ASSETS_DIR}")
            print(f"Full path: {file_path}")
            print(
                f"File exists: "
                f"{os.path.exists(file_path)}"
            )

            try:

                assets_content = os.listdir(
                    ASSETS_DIR
                )

                print(
                    f"Assets content: "
                    f"{assets_content}"
                )

            except Exception as e:

                print(
                    f"Cannot read Assets folder: "
                    f"{e}"
                )

            print("===================================")
            print("")


            # ==============================================
            # IMAGE INTROUVABLE
            # ==============================================

            if not os.path.exists(file_path):

                self._set_headers(
                    404,
                    "application/json"
                )

                self.wfile.write(
                    json.dumps({
                        "error": "Image not found",
                        "requested_file": filename
                    }).encode("utf-8")
                )

                return


            # ==============================================
            # CONTENT TYPE
            # ==============================================

            lower_file = filename.lower()

            if lower_file.endswith(".png"):

                content_type = "image/png"

            elif lower_file.endswith(
                (".jpg", ".jpeg")
            ):

                content_type = "image/jpeg"

            elif lower_file.endswith(".webp"):

                content_type = "image/webp"

            elif lower_file.endswith(".gif"):

                content_type = "image/gif"

            else:

                content_type = (
                    "application/octet-stream"
                )


            # ==============================================
            # ENVOI DE L'IMAGE
            # ==============================================

            self._set_headers(
                200,
                content_type
            )

            with open(
                file_path,
                "rb"
            ) as file:

                self.wfile.write(
                    file.read()
                )

            return


        # ==================================================
        # ÉTAPE 1 — DRIIVZ CHECK
        # ==================================================
        #
        # Exemple :
        #
        # /ads/check?property=193&country=ca
        #
        # 193 -> {"ads": 1}
        # 45  -> {"ads": 1}
        #
        # Autre -> {"ads": 0}
        #
        # ==================================================

        if path == "/ads/check":

            if property_id is None:

                self._set_headers(
                    400,
                    "application/json"
                )

                self.wfile.write(
                    json.dumps({
                        "error":
                        "Missing 'property' parameter"
                    }).encode("utf-8")
                )

                return


            has_ads = (
                1
                if property_id in ADS_BY_PROPERTY
                else 0
            )


            print(
                f"ADS CHECK | "
                f"Property: {property_id} | "
                f"Country: {country} | "
                f"Ads: {has_ads}"
            )


            self._set_headers(
                200,
                "application/json"
            )

            self.wfile.write(
                json.dumps({
                    "ads": has_ads
                }).encode("utf-8")
            )

            return


        # ==================================================
        # ÉTAPE 2 — DRIIVZ CONTENT
        # ==================================================
        #
        # 193 -> Car-Wash.png
        # 45  -> promo-combo.png
        #
        # ==================================================

        if path == "/ads/content":

            if property_id is None:

                self._set_headers(
                    400,
                    "application/json"
                )

                self.wfile.write(
                    json.dumps({
                        "error":
                        "Missing 'property' parameter"
                    }).encode("utf-8")
                )

                return


            # Cherche l'image associée au Property ID

            ad_image = ADS_BY_PROPERTY.get(
                property_id
            )


            # ==============================================
            # AUCUNE PUB CONFIGURÉE
            # ==============================================

            if ad_image is None:

                self._set_headers(
                    404,
                    "application/json"
                )

                self.wfile.write(
                    json.dumps({
                        "error":
                        "No ad configured for this property"
                    }).encode("utf-8")
                )

                return


            print(
                f"ADS CONTENT | "
                f"Property: {property_id} | "
                f"Country: {country} | "
                f"Image: {ad_image}"
            )


            # ==============================================
            # HTML ENVOYÉ À DRIIVZ
            # ==============================================

            html_content = f"""
<!DOCTYPE html>

<html lang="fr">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
Couche-Tard Recharge
</title>

<style>

html,
body {{
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
                html_content.encode(
                    "utf-8"
                )
            )

            return


        # ==================================================
        # HOME / HEALTH CHECK
        # ==================================================

        if path == "/":

            self._set_headers(
                200,
                "text/plain; charset=utf-8"
            )

            self.wfile.write(
                b"Driivz Ads Server - OK"
            )

            return


        # ==================================================
        # 404
        # ==================================================

        self._set_headers(
            404,
            "application/json"
        )

        self.wfile.write(
            json.dumps({
                "error": "Not found"
            }).encode("utf-8")
        )


# ==========================================================
# SERVER
# ==========================================================

def run_server(
    server_class=HTTPServer,
    handler_class=DriivzAdHandler
) -> None:

    port = int(
        os.getenv(
            "PORT",
            "8000"
        )
    )

    server_address = (
        "",
        port
    )

    httpd = server_class(
        server_address,
        handler_class
    )


    print("")
    print("====================================")
    print("DRIIVZ ADS SERVER")
    print("====================================")
    print(f"Port: {port}")
    print(f"Base directory: {BASE_DIR}")
    print(f"Assets directory: {ASSETS_DIR}")

    try:

        print(
            f"Assets found: "
            f"{os.listdir(ASSETS_DIR)}"
        )

    except Exception as e:

        print(
            f"ERROR reading Assets: {e}"
        )

    print("")

    print("Configured properties:")

    for property_id, image in ADS_BY_PROPERTY.items():

        print(
            f"  Property {property_id}"
            f" -> {image}"
        )

    print("====================================")
    print("")


    try:

        httpd.serve_forever()

    except KeyboardInterrupt:

        pass

    finally:

        httpd.server_close()


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":

    run_server()
