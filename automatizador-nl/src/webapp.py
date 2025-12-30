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
#   CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Indicamos a Flask dónde están los templates (carpeta superior)
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
app.config["UPLOAD_FOLDER"] = UPLOADS_DIR


# ============================================================
#   HOME – PANTALLA PRINCIPAL (DISEÑO ACTUALIZADO)
# ============================================================

@app.route("/", methods=["GET"])
def index():
    html = """
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Automatizador de Newsletters</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            :root { 
                --primary: #FF002D; 
                --primary-hover: #D60026; 
                --bg: #F4F7F6; 
                --text: #2c3e50; 
            }
            body { 
                font-family: 'Poppins', Arial, sans-serif; 
                background: var(--bg); 
                margin: 0; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh; 
                color: var(--text); 
            }
            
            .container {
                background: white;
                padding: 45px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.08);
                width: 100%;
                max-width: 480px;
                text-align: center;
            }

            h2 { 
                margin-bottom: 30px; 
                font-weight: 700; 
                color: #111; 
                letter-spacing: -0.5px; 
            }
            
            /* Tarjeta Scraper */
            .scraper-card {
                background: linear-gradient(135deg, #fff0f2 0%, #fff 100%);
                border: 2px dashed #ffb3c0;
                border-radius: 12px;
                padding: 25px;
                margin-bottom: 35px;
                transition: all 0.2s;
                cursor: pointer;
            }
            .scraper-card:hover { 
                transform: translateY(-3px); 
                border-color: var(--primary); 
                box-shadow: 0 5px 15px rgba(255, 0, 45, 0.1);
            }
            .scraper-link {
                display: block; 
                text-decoration: none; 
                color: var(--primary); 
                font-weight: 700; 
                font-size: 1.1rem;
            }
            .scraper-hint { 
                display: block; 
                font-size: 0.85rem; 
                color: #666; 
                margin-top: 8px; 
                font-weight: 400; 
            }

            /* Formulario */
            form { text-align: left; }
            label { 
                display: block; 
                font-weight: 600; 
                margin-bottom: 8px; 
                font-size: 0.9rem; 
                color: #333; 
            }
            
            input[type="text"], select, input[type="file"] {
                width: 100%;
                padding: 14px;
                margin-bottom: 20px;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                font-family: inherit;
                font-size: 0.95rem;
                background: #fff;
                transition: border-color 0.2s, box-shadow 0.2s;
                box-sizing: border-box;
            }
            input:focus, select:focus {
                border-color: var(--primary);
                outline: none;
                box-shadow: 0 0 0 3px rgba(255, 0, 45, 0.15);
            }

            .btn-main {
                width: 100%;
                padding: 16px;
                background: var(--primary);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.2s, transform 0.1s;
                box-shadow: 0 4px 15px rgba(255, 0, 45, 0.3);
            }
            .btn-main:hover { 
                background: var(--primary-hover); 
                transform: translateY(-1px);
            }
            
            .divider { 
                height: 1px; 
                background: #eee; 
                margin: 30px 0; 
                position: relative; 
            }
            .divider span { 
                position: absolute; 
                top: -10px; 
                left: 50%; 
                transform: translateX(-50%); 
                background: white; 
                padding: 0 10px; 
                color: #aaa; 
                font-size: 0.8rem; 
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
        </style>
    </head>
    <body>

        <div class="container">
            <h2>Generador de Newsletters</h2>

            <div class="scraper-card" onclick="window.location.href='/scraper'">
                <a href="/scraper" class="scraper-link">Usar Importador Automático</a>
                <span class="scraper-hint">Pega URLs y deja que la IA trabaje por ti</span>
            </div>

            <div class="divider"><span>O sube tu CSV</span></div>

            <form action="/generate" method="POST" enctype="multipart/form-data">
                
                <label>Archivo CSV</label>
                <input type="file" name="csv_file" required accept=".csv">

                <label>Diseño de la Card</label>
                <select name="card_mode" required>
                    <option value="urbano">🏙️ Ocio Urbano (Completo)</option>
                    <option value="vacacional">✈️ Ocio Vacacional (Compacto)</option>
                </select>

                <label>Título Interno (Campaña UTM)</label>
                <input type="text" name="newsletter_title" placeholder="Ej: Escapadas_Noviembre_2025">

                <button type="submit" class="btn-main">Generar HTML</button>
            </form>
        </div>

    </body>
    </html>
    """
    return render_template_string(html)


# ============================================================
#   RUTA 1: GENERAR NEWSLETTER DESDE CSV (Fase 1)
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
#   RUTA 2: SCRAPER (Fase 2)
# ============================================================

@app.route("/scraper", methods=["GET"])
def scraper_index():
    """Muestra el formulario para pegar URLs"""
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
                'description': 'Bloqueo o URL errónea. Revisa el enlace.',
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
    
    # Recoger datos de Configuración Global (Panel Superior)
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
    
    # 3. Iteramos los productos editados
    for i in range(1, total_items + 1):
        idx = str(i)
        
        rating_val = request.form.get(f"rating_{idx}", "")
        rating_final = f"{rating_val} - Excelente" if rating_val and "-" not in rating_val else rating_val

        # Recogemos los campos nuevos (Separator y CTA)
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
            separator, "", cta_text 
        ])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=input_scraped.csv"
    output.headers["Content-type"] = "text/csv"
    return output


# ============================================================
#   SERVIR ARCHIVOS
# ============================================================

@app.route("/uploads/<path:filename>")
def uploaded_files(filename):
    return send_file(os.path.join(app.config["UPLOAD_FOLDER"], filename))


if __name__ == "__main__":
    app.run(debug=True)