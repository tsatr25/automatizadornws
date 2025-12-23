import os
from flask import Flask, render_template_string, request, send_file

from src.csv_parser import csv_to_newsletter_dict
from src.renderer import render_newsletter, apply_utm_tracking


# ============================================================
#   CONFIG
# ============================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOADS_DIR


# ============================================================
#   HOME – FORMULARIO
# ============================================================

@app.route("/", methods=["GET"])
def index():
    html = """
    <html>
    <head>
        <title>Generador Newsletter Atrápalo</title>
        <style>
            body { font-family: Arial; background:#f5f5f5; }
            .box { 
                background:white; 
                padding:30px; 
                border-radius:10px; 
                max-width:500px; 
                margin:50px auto;
                box-shadow:0 4px 20px rgba(0,0,0,0.1);
            }
            label { font-weight:bold; display:block; margin-top:15px; }
            input, select {
                width:100%; 
                padding:10px;
                border-radius:6px;
                border:1px solid #ccc;
            }
            button {
                width:100%;
                padding:12px;
                margin-top:25px;
                font-size:16px;
                font-weight:bold;
                background:#e6002c;
                color:white;
                border:none;
                border-radius:6px;
                cursor:pointer;
            }
            button:hover { background:#ff002d; }
        </style>
    </head>
    <body>

        <div class="box">
            <h2>Generador de Newsletter Atrápalo</h2>

            <form action="/generate" method="POST" enctype="multipart/form-data">

                <label>Subir archivo CSV:</label>
                <input type="file" name="csv_file" required>

                <label>Tipo de card:</label>
                <select name="card_mode" required>
                    <option value="urbano">Ocio urbano (completo)</option>
                    <option value="vacacional">Ocio vacacional (compacto)</option>
                </select>

                <label>Título del newsletter (OBLIGATORIO):</label>
                <input type="text" name="newsletter_title" placeholder="Ej: Escapadas Madrid Noviembre">

                <button type="submit">Generar Newsletter</button>
            </form>
        </div>

    </body>
    </html>
    """
    return render_template_string(html)


# ============================================================
#   GENERAR NEWSLETTER
# ============================================================

@app.route("/generate", methods=["POST"])
def generate_newsletter():

    uploaded_file = request.files["csv_file"]
    card_mode = request.form.get("card_mode", "urbano")
    newsletter_title = request.form.get("newsletter_title", "").strip()

    csv_path = os.path.join(app.config["UPLOAD_FOLDER"], "input.csv")
    uploaded_file.save(csv_path)

    # --- PARSE CSV ---
    newsletter_data = csv_to_newsletter_dict(csv_path)
    newsletter_data["card_mode"] = card_mode
    newsletter_data["title"] = newsletter_title

    # --- EXTRAER CONDICIONES ---
    conditions_text = ""
    for card in newsletter_data["cards"]:
        if card.get("conditions"):
            conditions_text = card["conditions"]
            break

    newsletter_data["conditions"] = conditions_text

    # --- GENERAR HTML BASE ---
    html_raw = render_newsletter(newsletter_data)

    # --- APLICAR UTMs AUTOMÁTICAS ---
    html_output = apply_utm_tracking(html_raw, newsletter_title)

    # --- GUARDAR PREVIEW ---
    preview_path = os.path.join(app.config["UPLOAD_FOLDER"], "preview.html")
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    # --- PÁGINA DE RESULTADO ---
    result_html = f"""
    <html>
    <head>
        <title>Newsletter Generada</title>
        <style>
            body {{ font-family: Arial; padding:20px; }}
            textarea {{
                width:100%;
                height:300px;
                padding:10px;
                font-family: monospace;
                white-space: pre;
                border-radius:8px;
                border:1px solid #ccc;
            }}
            .buttons {{
                margin-top:20px;
            }}
            button {{
                padding:10px 20px;
                margin-right:15px;
                font-size:14px;
                cursor:pointer;
                border:none;
                border-radius:6px;
            }}
            .copy-btn {{ background:#e6002c; color:white; }}
            .back-btn {{ background:#ddd; }}
            iframe {{
                width:100%;
                height:600px;
                border:1px solid #ccc;
                border-radius:8px;
                margin-top:30px;
            }}
        </style>

        <script>
            function copyHTML() {{
                var textarea = document.getElementById("htmlcode");
                textarea.select();
                document.execCommand("copy");
                alert("Código HTML copiado al portapapeles.");
            }}
        </script>
    </head>

    <body>
        <h2>Newsletter generada correctamente</h2>

        <h3>1. Código HTML</h3>
        <textarea id="htmlcode">{html_output.replace("<", "&lt;").replace(">", "&gt;")}</textarea>

        <div class="buttons">
            <button class="copy-btn" onclick="copyHTML()">Copiar HTML</button>
            <a href="/"><button class="back-btn">Volver</button></a>
        </div>

        <h3>2. Vista previa</h3>
        <iframe src="/uploads/preview.html"></iframe>
    </body>
    </html>
    """

    return render_template_string(result_html)


# ============================================================
#   SERVIR PREVIEW
# ============================================================

@app.route("/uploads/<path:filename>")
def uploaded_files(filename):
    return send_file(os.path.join(app.config["UPLOAD_FOLDER"], filename))


# ============================================================
#   MAIN
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)
