import os
import csv
import io
import time
import random
from flask import Flask, render_template_string, request, send_file, render_template, make_response

from src.csv_parser import csv_to_newsletter_dict
from src.renderer import render_newsletter, apply_utm_tracking
from src.scraper import get_atrapalo_data


# ============================================================
#   CONFIG
# ============================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
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
            .scraper-link {
                display: block;
                text-align: center;
                margin-bottom: 20px;
                color: #e6002c;
                font-weight: bold;
                text-decoration: none;
                border: 2px dashed #e6002c;
                padding: 10px;
                border-radius: 6px;
                background: #fff5f5;
            }
            .scraper-link:hover { background: #ffebeb; }
        </style>
    </head>
    <body>

        <div class="box">
            
            <a href="/scraper" class="scraper-link">⚡ Ir al Importador Automático (Scraper)</a>

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
#   GENERAR NEWSLETTER (FASE 1)
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
#   NUEVO: SCRAPER & IMPORTADOR (FASE 2)
# ============================================================

@app.route("/scraper", methods=["GET"])
def scraper_index():
    return render_template("scraper_form.html")

@app.route("/scraper/review", methods=["POST"])
def scraper_review():
    """Procesa las URLs con pausa anti-bloqueo y gestión de errores"""
    raw_urls = request.form.get("urls", "").strip()
    url_list = [u.strip() for u in raw_urls.split('\n') if u.strip()]
    
    scraped_items = []
    
    for i, url in enumerate(url_list):
        print(f"Procesando {i+1}/{len(url_list)}: {url}")
        
        # 1. Llamamos al scraper
        data = get_atrapalo_data(url)
        
        if data:
            scraped_items.append(data)
        else:
            # 2. SI FALLA: Item de error
            scraped_items.append({
                'url': url,
                'title': '❌ ERROR DE LECTURA',
                'description': 'Bloqueo o URL errónea.',
                'image': '', 
                'price': '0', 'price_old': '', 'discount': '', 
                'metadata_1': '', 'metadata_2': '', 'rating': '', 'tag': 'Sin tag'
            })
        
        # 3. PAUSA HUMANIZADORA
        time.sleep(random.uniform(2, 4))
    
    return render_template("scraper_review.html", items=scraped_items)

@app.route("/scraper/download", methods=["POST"])
def scraper_download():
    """Genera el CSV final con cabeceras de configuración y productos"""
    try:
        total_items = int(request.form.get("total_items", 0))
    except:
        total_items = 0
    
    # Recoger datos de Configuración Global
    c_loc = request.form.get("csv_localizacion", "")
    c_prod = request.form.get("csv_producto", "")
    c_envio = request.form.get("csv_tipo_envio", "")
    c_fenvio = request.form.get("csv_fenvio", "")
    c_header = request.form.get("csv_header", "")
    c_link_h = request.form.get("csv_link_header", "")
    c_asunto = request.form.get("csv_asunto", "")
    c_pre = request.form.get("csv_preheader", "")
    c_txt_btn = request.form.get("csv_txt_boton", "")
    c_link_f = request.form.get("csv_link_footer", "")
    c_banner = request.form.get("csv_banner", "")
    c_link_b = request.form.get("csv_link_banner", "")
    c_cond = request.form.get("csv_condiciones", "")

    # Crear CSV en memoria
    si = io.StringIO()
    writer = csv.writer(si)
    
    # 1. Escribir CABECERAS DE CONFIGURACIÓN
    empty = [""] * 12 
    writer.writerow(["LOCALIZACIÓN:", c_loc] + empty)
    writer.writerow(["PRODUCTO:", c_prod] + empty)
    writer.writerow(["TIPO DE ENVÍO:", c_envio] + empty)
    writer.writerow(["FENVIO:", c_fenvio] + empty)
    writer.writerow(["HEADER:", c_header] + empty)
    writer.writerow(["LINK HEADER:", c_link_h] + empty)
    writer.writerow(["ASUNTO:", c_asunto] + empty)
    writer.writerow(["PREHEADER:", c_pre] + empty)
    writer.writerow(["TXT_BOTON_FOOTER:", c_txt_btn] + empty)
    writer.writerow(["LINK_FOOTER:", c_link_f] + empty)
    writer.writerow(["BANNER_FOOTER:", c_banner] + empty)
    writer.writerow(["LINK_BANNER_FOOTER:", c_link_b] + empty)
    writer.writerow(["CONDICIONES_FOOTER:", c_cond] + empty)
    
    writer.writerow([]) 
    writer.writerow([]) 
    writer.writerow([]) 
    
    # 2. Cabecera REAL
    writer.writerow([
        "Orden", "Nombre Oferta", "Metadato 1", "Metadato 2", "Descripción", 
        "URL foto", "URL oferta", "Descuento", "Precio", "Precio ATR", 
        "TAGS", "RATING", "SEPARADOR", "SEPARADOR IMG", "CTA"
    ])
    
    # 3. Iteramos los productos
    for i in range(1, total_items + 1):
        idx = str(i)
        
        rating_val = request.form.get(f"rating_{idx}", "")
        rating_final = f"{rating_val} - Excelente" if rating_val and "-" not in rating_val else rating_val

        # Recogemos los campos nuevos
        separator = request.form.get(f"separator_{idx}", "")
        cta_text = request.form.get(f"cta_{idx}", "Ver plan")

        writer.writerow([
            request.form.get(f"order_{idx}"),
            request.form.get(f"title_{idx}"),
            request.form.get(f"meta1_{idx}"),
            request.form.get(f"meta2_{idx}"),
            request.form.get(f"desc_{idx}"),
            request.form.get(f"image_{idx}"),
            request.form.get(f"url_{idx}"),
            request.form.get(f"discount_{idx}"),
            request.form.get(f"price_old_{idx}"),
            request.form.get(f"price_{idx}"),
            request.form.get(f"tag_{idx}", "Sin tag"),
            rating_final,
            separator, "", cta_text # Separador y CTA integrados
        ])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=input_scraped.csv"
    output.headers["Content-type"] = "text/csv"
    return output


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