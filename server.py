import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs


# ==========================================================
# CONFIGURATION DES PUBLICITÉS
# ==========================================================
#
# 1. MAGASINS ACCEPTÉS
# Ajouter ici les Property ID Driivz qui doivent afficher une publicité.
#
# Exemple :
# "45"       = pub activée
# "193"      = pub activée
# "6001124"  = pub activée
#
# Tous les autres magasins recevront : {"ads": 0}
#
# ----------------------------------------------------------
# 2. IMAGE AFFICHÉE
# L'image doit être dans le dossier Assets.
#
# Exemple :
# Assets/promo.png
#
# Pour changer de publicité, change seulement cette ligne :
# CURRENT_AD = "promo.png"
# ==========================================================

ADS_ENABLED_PROPERTIES = {
    "193",
    "45",
}

CURRENT_AD = "promo.png"


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
        country = query.get("country", [None])[0]

        # ==========================================================
        # DOSSIER DES IMAGES
        # ==========================================================
        #
        # Toutes les images doivent être ici :
        #
        # Assets/
        #   promo.png
        #   breakfast.png
        #   pizza.png
        #
        # Exemple d'URL :
        # /Assets/promo.png
        # ==========================================================

        if path.startswith("/Assets/"):
            file_path = "." + path

            if not os.path.exists(file_path):
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Image not found"}).encode())
                return

            if file_path.endswith(".png"):
                content_type = "image/png"
            elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                content_type = "image/jpeg"
            elif file_path.endswith(".webp"):
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
        # Driivz appelle :
        # /ads/check?property=45&country=CA
        #
        # Si le property est dans ADS_ENABLED_PROPERTIES :
        # réponse : {"ads": 1}
        #
        # Sinon :
        # réponse : {"ads": 0}
        # ==========================================================

        if path == "/ads/check":
            if property_id is None:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'property' parameter"}).encode())
                return

            has_ads = 1 if property_id in ADS_ENABLED_PROPERTIES else 0

            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"ads": has_ads}).encode())
            return

        # ==========================================================
        # ÉTAPE 2 - DRIIVZ CONTENT
        # ==========================================================
        #
        # Driivz appelle :
        # /ads/content?property=45&country=CA
        #
        # Ici, on affiche l'image choisie dans CURRENT_AD.
        #
        # Pour changer la publicité :
        # 1. Ajouter l'image dans Assets
        # 2. Changer CURRENT_AD plus haut dans le fichier
        # ==========================================================

        if path == "/ads/content":
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
    background: #ffffff;
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
<img src="/Assets/{CURRENT_AD}" alt="Promotion Couche-Tard">
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
    print(f"Serving on port {port}...")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run_server()