import os
import csv
import io
import time
import random
import json
import glob
import re
from flask import Flask, render_template_string, request, send_file, render_template, make_response, redirect, url_for, jsonify

from src.csv_parser import csv_to_newsletter_dict
from src.renderer import render_newsletter
from src.scraper import get_atrapalo_data
from src.marketing import TrackingGenerator, ImageResizer


# ============================================================
#   CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
DRAFTS_DIR = os.path.join(BASE_DIR, "drafts")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DRAFTS_DIR, exist_ok=True)

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
app.config["UPLOAD_FOLDER"] = UPLOADS_DIR
app.config["DRAFTS_FOLDER"] = DRAFTS_DIR


# ============================================================
#   HOME: PANEL DE CONTROL
# ============================================================

@app.route("/", methods=["GET"])
def index():
    html = """
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Panel de Automatización</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root { 
                --primary: #FF002D; 
                --primary-dark: #D60026;
                --text-main: #1F2937;
                --text-sec: #6B7280;
                --bg: #F3F4F6; 
                --border: #E5E7EB;
            }
            body { 
                font-family: 'Poppins', sans-serif; 
                background: var(--bg); 
                margin: 0; 
                color: var(--text-main); 
                display: flex; 
                justify-content: center; 
                padding-top: 60px;
                min-height: 100vh;
            }
            
            .container {
                max-width: 960px;
                width: 100%;
                padding: 0 20px;
            }

            header {
                margin-bottom: 30px;
                border-bottom: 1px solid #E5E7EB;
                padding-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .header-info { flex: 1; }

            h1 { 
                font-weight: 600; 
                font-size: 1.5rem; 
                margin: 0 0 5px 0; 
                color: #111;
            }
            
            .subtitle {
                color: var(--text-sec);
                font-size: 0.95rem;
                margin: 0;
            }

            .grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 24px;
            }

            .card {
                background: white;
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 32px;
                display: flex;
                flex-direction: column;
            }

            .card-title {
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 12px;
                color: #111;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .badge-new {
                background: #EFF6FF;
                color: #2563EB;
                font-size: 0.7rem;
                padding: 2px 8px;
                border-radius: 4px;
                font-weight: 600;
                text-transform: uppercase;
            }

            .card-desc {
                font-size: 0.9rem;
                color: var(--text-sec);
                margin-bottom: 24px;
                line-height: 1.6;
                flex-grow: 1;
            }

            /* FORM ELEMENTS */
            label {
                display: block;
                font-size: 0.8rem;
                font-weight: 500;
                margin-bottom: 6px;
                color: #374151;
            }

            input[type="text"], input[type="file"], select {
                width: 100%;
                padding: 10px 12px;
                margin-bottom: 16px;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                font-size: 0.9rem;
                font-family: inherit;
                box-sizing: border-box;
                background: #F9FAFB;
            }
            
            input:focus, select:focus {
                outline: none;
                border-color: var(--primary);
                background: white;
            }

            /* BOTONES */
            .btn {
                display: inline-flex;
                justify-content: center;
                align-items: center;
                width: 100%;
                padding: 12px 20px;
                background: var(--primary);
                color: white;
                font-size: 0.95rem;
                font-weight: 500;
                border-radius: 6px;
                border: none;
                text-decoration: none;
                cursor: pointer;
                transition: background 0.2s;
                box-sizing: border-box;
            }
            
            .btn:hover {
                background: var(--primary-dark);
            }
            
            .btn-outline {
                background: white;
                border: 1px solid var(--primary);
                color: var(--primary);
            }
            
            .btn-outline:hover {
                background: #FFF5F5;
            }

            .btn-small {
                width: fit-content !important;
                padding: 12px 20px !important;
                font-size: 0.9rem !important;
                height: auto !important;
                margin-left: auto;
            }

            @media (max-width: 768px) {
                .grid { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>

        <div class="container">
            <header>
                <div class="header-info">
                    <h1>Panel de Control</h1>
                    <p class="subtitle">Sistema de gestión y automatización de newsletters</p>
                </div>
                <a href="/marketing" class="btn btn-outline btn-small">Marketing Tools</a>
            </header>

            <div class="grid">
                
                <div class="card">
                    <div class="card-title">
                        Generador de NWS por URL
                    </div>
                    <div class="card-desc">
                        Herramienta para gestionar y automatizar la creación de newsletters a partir de URLs de Atrápalo.
                        <ul style="padding-left: 20px; margin-top: 10px; margin-bottom: 0;">
                            <li>Importación automática desde URLs.</li>
                            <li>Gestión de borradores y estados.</li>
                            <li>Actualización de precios en tiempo real.</li>
                        </ul>
                    </div>
                    <a href="/scraper" class="btn">Acceder al Gestor</a>
                </div>

                <div class="card">
                    <div class="card-title">Generador de NWS por CSV</div>
                    <div class="card-desc">
                        Utilidad para procesar un archivo CSV previamente formateado y obtener el código HTML final.
                    </div>
                    
                    <form action="/generate" method="POST" enctype="multipart/form-data">
                        
                        <label>Archivo CSV</label>
                        <input type="file" name="csv_file" required accept=".csv">

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                            <div>
                                <label>Diseño</label>
                                <select name="card_mode">
                                    <option value="urbano">Ocio Urbano</option>
                                    <option value="vacacional">Vacacional</option>
                                </select>
                            </div>
                            <div>
                                <label>Campaña (UTM)</label>
                                <input type="text" name="newsletter_title" placeholder="Ej: Promo_Enero">
                            </div>
                        </div>

                        <button type="submit" class="btn btn-outline">Generar HTML</button>
                    </form>
                </div>
            </div>

        </div>

    </body>
    </html>
    """
    return render_template_string(html)


# ============================================================
#   FASE 1: GENERAR HTML
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

    conditions_text = ""
    for card in newsletter_data["cards"]:
        if card.get("conditions"):
            conditions_text = card["conditions"]
            break
    newsletter_data["conditions"] = conditions_text

    # --- GENERAR HTML BASE ---
    html_raw = render_newsletter(newsletter_data)
    html_output = html_raw 

    preview_path = os.path.join(app.config["UPLOAD_FOLDER"], "preview.html")
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    result_html = f"""
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <title>Resultado</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Poppins', sans-serif; padding: 40px; background: #F3F4F6; color: #1F2937; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; border: 1px solid #E5E7EB; }}
            h2 {{ margin-top: 0; font-size: 1.2rem; margin-bottom: 20px; }}
            textarea {{ width: 100%; height: 250px; padding: 15px; font-family: monospace; border: 1px solid #D1D5DB; border-radius: 6px; box-sizing: border-box; background: #F9FAFB; }}
            textarea:focus {{ outline: none; border-color: #FF002D; }}
            .actions {{ margin-top: 20px; display: flex; gap: 10px; }}
            .btn {{ padding: 10px 20px; background: #FF002D; color: white; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; text-decoration: none; }}
            .btn:hover {{ background: #D60026; }}
            .btn-sec {{ background: white; border: 1px solid #D1D5DB; color: #374151; }}
            .btn-sec:hover {{ background: #F3F4F6; }}
        </style>
        <script>
            function copy() {{
                document.getElementById("code").select();
                document.execCommand("copy");
                alert("Código copiado al portapapeles.");
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h2>Newsletter Generada</h2>
            <textarea id="code">{html_output.replace("<", "&lt;")}</textarea>
            <div class="actions">
                <button class="btn" onclick="copy()">Copiar Código</button>
                <a href="/uploads/preview.html" target="_blank" class="btn btn-sec">Vista Previa</a>
                <a href="/" class="btn btn-sec" style="margin-left: auto;">Volver al Panel</a>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(result_html)


# ============================================================
#   FASE 2: SCRAPER Y KANBAN
# ============================================================

@app.route("/scraper", methods=["GET"])
def scraper_index():
    drafts_pending = []
    drafts_ready = []
    # drafts_archived ya no se carga aquí
    
    if os.path.exists(DRAFTS_DIR):
        files = glob.glob(os.path.join(DRAFTS_DIR, "*.json"))
        files.sort(key=os.path.getmtime, reverse=True)
        for f in files:
            filename = os.path.basename(f)
            try:
                with open(f, "r", encoding="utf-8") as jf:
                    content = json.load(jf)
                    status = content.get("meta", {}).get("status", "pending")
                    
                    if status == "ready":
                        drafts_ready.append(filename)
                    elif status == "archived":
                        pass
                    else:
                        drafts_pending.append(filename)
            except:
                drafts_pending.append(filename)
            
    return render_template("scraper_form.html", 
                           drafts_pending=drafts_pending, 
                           drafts_ready=drafts_ready)

# --- NUEVA RUTA: ARCHIVO ---
@app.route("/scraper/archive", methods=["GET"])
def scraper_archive():
    drafts_archived = []
    
    if os.path.exists(DRAFTS_DIR):
        files = glob.glob(os.path.join(DRAFTS_DIR, "*.json"))
        files.sort(key=os.path.getmtime, reverse=True)
        for f in files:
            filename = os.path.basename(f)
            try:
                with open(f, "r", encoding="utf-8") as jf:
                    content = json.load(jf)
                    status = content.get("meta", {}).get("status", "pending")
                    
                    if status == "archived":
                        drafts_archived.append({
                            "filename": filename,
                            "updated": time.ctime(os.path.getmtime(f))
                        })
            except:
                pass
            
    return render_template("scraper_archive.html", drafts_archived=drafts_archived)


@app.route("/scraper/review", methods=["POST"])
def scraper_review():
    raw_urls = request.form.get("urls", "").strip()
    url_list = [u.strip() for u in raw_urls.split('\n') if u.strip()]
    
    scraped_items = []
    for i, url in enumerate(url_list):
        print(f"Procesando {i+1}/{len(url_list)}: {url}")
        data = get_atrapalo_data(url)
        if data:
            scraped_items.append(data)
        else:
            scraped_items.append({
                'url': url, 'title': 'ERROR DE LECTURA', 'description': 'Revisar URL.',
                'image': '', 'price': '', 'price_old': '', 'discount': '', 'metadata_1': '', 'metadata_2': '', 'rating': '', 'tag': ''
            })
        time.sleep(random.uniform(2, 4))
    
    default_config = {
        "csv_localizacion": "",
        "csv_producto": "MIXOU",
        "csv_tipo_envio": "La agenda de Enero",
        "csv_fenvio": "",
        "csv_header": "https://nws-images-atrapalo.s3.amazonaws.com/2026/W2/0701_MIXOU/HeaderAgendadelMes.png",
        "csv_link_header": "https://www.atrapalo.com/actividades/barcelona/desde-07-01-2026-hasta-31-01-2026/",
        "csv_asunto": "¿Sin plan para enero, @name?",
        "csv_preheader": "Te traemos lo mejor del mes para que sueltes el sofá.",
        "csv_txt_boton": "Sigue explorando",
        "csv_link_footer": "https://www.atrapalo.com/actividades/barcelona/desde-07-01-2026-hasta-31-01-2026/",
        "csv_banner": "https://nws-images-atrapalo.s3.amazonaws.com/2026/W2/0701_MIXOU/Footer_RealidadVirtual.png",
        "csv_link_banner": "https://www.atrapalo.com/actividades/promociones/experiencias-que-te-sacan-del-mundo-real/barcelona/",
        "csv_condiciones": ""
    }
    
    return render_template("scraper_review.html", items=scraped_items, config=default_config)

@app.route("/update_prices", methods=["POST"])
def update_prices():
    try:
        total_items = int(request.form.get("total_items", 0))
    except:
        total_items = 0
        
    draft_name = request.form.get("draft_name", "")
    current_status = request.form.get("status_choice", "pending")

    config = {
        "csv_localizacion": request.form.get("csv_localizacion"),
        "csv_producto": request.form.get("csv_producto"),
        "csv_tipo_envio": request.form.get("csv_tipo_envio"),
        "csv_fenvio": request.form.get("csv_fenvio"),
        "csv_header": request.form.get("csv_header"),
        "csv_link_header": request.form.get("csv_link_header"),
        "csv_asunto": request.form.get("csv_asunto"),
        "csv_preheader": request.form.get("csv_preheader"),
        "csv_txt_boton": request.form.get("csv_txt_boton"),
        "csv_link_footer": request.form.get("csv_link_footer"),
        "csv_banner": request.form.get("csv_banner"),
        "csv_link_banner": request.form.get("csv_link_banner"),
        "csv_condiciones": request.form.get("csv_condiciones")
    }

    updated_items = []
    for i in range(1, total_items + 1):
        idx = str(i)
        url = request.form.get(f"url_{idx}")
        item = {
            "order": request.form.get(f"order_{idx}"),
            "title": request.form.get(f"title_{idx}"),
            "metadata_1": request.form.get(f"meta1_{idx}"),
            "metadata_2": request.form.get(f"meta2_{idx}"),
            "description": request.form.get(f"desc_{idx}"),
            "image": request.form.get(f"image_{idx}"),
            "url": url,
            "tag": request.form.get(f"tag_{idx}"),
            "separator": request.form.get(f"separator_{idx}"),
            "cta": request.form.get(f"cta_{idx}"),
            "price": request.form.get(f"price_{idx}"),
            "price_old": request.form.get(f"price_old_{idx}"),
            "discount": request.form.get(f"discount_{idx}"),
            "rating": request.form.get(f"rating_{idx}")
        }
        
        if url and "atrapalo.com" in url:
            fresh_data = get_atrapalo_data(url)
            if fresh_data:
                item["price"] = fresh_data.get("price", item["price"])
                item["price_old"] = fresh_data.get("price_old", item["price_old"])
                item["discount"] = fresh_data.get("discount", item["discount"])
                item["rating"] = fresh_data.get("rating", item["rating"])
                if fresh_data.get("tag"): item["tag"] = fresh_data.get("tag")
            time.sleep(random.uniform(1, 2))
            
        updated_items.append(item)

    return render_template("scraper_review.html", 
                           items=updated_items, 
                           config=config, 
                           draft_name=draft_name,
                           current_status=current_status,
                           message="Precios actualizados correctamente.")

@app.route("/save_draft", methods=["POST"])
def save_draft():
    try:
        total_items = int(request.form.get("total_items", 0))
    except:
        total_items = 0
        
    draft_name = request.form.get("draft_name", "").strip()
    if not draft_name:
        draft_name = f"borrador_{int(time.time())}"
    if not draft_name.endswith(".json"):
        draft_name += ".json"

    status_value = request.form.get("status_choice", "pending")

    config = {
        "csv_localizacion": request.form.get("csv_localizacion"),
        "csv_producto": request.form.get("csv_producto"),
        "csv_tipo_envio": request.form.get("csv_tipo_envio"),
        "csv_fenvio": request.form.get("csv_fenvio"),
        "csv_header": request.form.get("csv_header"),
        "csv_link_header": request.form.get("csv_link_header"),
        "csv_asunto": request.form.get("csv_asunto"),
        "csv_preheader": request.form.get("csv_preheader"),
        "csv_txt_boton": request.form.get("csv_txt_boton"),
        "csv_link_footer": request.form.get("csv_link_footer"),
        "csv_banner": request.form.get("csv_banner"),
        "csv_link_banner": request.form.get("csv_link_banner"),
        "csv_condiciones": request.form.get("csv_condiciones")
    }

    items = []
    for i in range(1, total_items + 1):
        idx = str(i)
        items.append({
            "order": request.form.get(f"order_{idx}"),
            "title": request.form.get(f"title_{idx}"),
            "metadata_1": request.form.get(f"meta1_{idx}"),
            "metadata_2": request.form.get(f"meta2_{idx}"),
            "description": request.form.get(f"desc_{idx}"),
            "image": request.form.get(f"image_{idx}"),
            "url": request.form.get(f"url_{idx}"),
            "discount": request.form.get(f"discount_{idx}"),
            "price_old": request.form.get(f"price_old_{idx}"),
            "price": request.form.get(f"price_{idx}"),
            "tag": request.form.get(f"tag_{idx}"),
            "rating": request.form.get(f"rating_{idx}"),
            "separator": request.form.get(f"separator_{idx}"),
            "cta": request.form.get(f"cta_{idx}")
        })

    data_to_save = {
        "meta": {"status": status_value, "updated_at": time.time()},
        "config": config,
        "items": items
    }
    
    with open(os.path.join(DRAFTS_DIR, draft_name), "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        
    return redirect(url_for('scraper_index'))

# --- API DRAG & DROP ---
@app.route("/api/update_status", methods=["POST"])
def api_update_status():
    data = request.json
    filename = data.get("filename")
    new_status = data.get("status")
    
    if not filename or not new_status:
        return jsonify({"error": "Faltan datos"}), 400
        
    filepath = os.path.join(DRAFTS_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Archivo no encontrado"}), 404
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = json.load(f)
        
        content["meta"]["status"] = new_status
        content["meta"]["updated_at"] = time.time()
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=4, ensure_ascii=False)
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/load_draft/<filename>")
def load_draft(filename):
    filepath = os.path.join(DRAFTS_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        current_status = data.get("meta", {}).get("status", "pending")
        return render_template("scraper_review.html", 
                               items=data.get("items", []), 
                               config=data.get("config", {}), 
                               draft_name=filename,
                               current_status=current_status)
    else:
        return "Borrador no encontrado", 404

@app.route("/delete_draft/<filename>")
def delete_draft(filename):
    filepath = os.path.join(DRAFTS_DIR, filename)
    if os.path.exists(filepath):
        try: os.remove(filepath)
        except: pass
    
    # Redirigir según desde dónde se llame
    referer = request.headers.get("Referer", "")
    if "archive" in referer:
        return redirect(url_for('scraper_archive'))
    return redirect(url_for('scraper_index'))

def force_spanish_format(val):
    if not val: return ""
    val = str(val).replace("€", "").strip()
    if "," in val and "." not in val: return val
    try:
        f = float(val)
        usa = "{:,.2f}".format(f)
        if usa.endswith(".00"): usa = "{:,.0f}".format(f)
        return usa.replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return val

def inject_tracking(url, campaign_name, date_str):
    if not url: return ""
    base_url = url.split("?")[0]
    
    # LÓGICA HÍBRIDA:
    # 1. Si es HOTEL -> Usar fecha (ignorar ID)
    if "/hoteles/" in base_url or "/hotel/" in base_url:
        if date_str: identifier = date_str.replace("-", "")
        else: identifier = time.strftime("%Y%m%d")
        
    # 2. Si es OCIO -> Usar ID si existe
    else:
        match = re.search(r"_(e|a)(\d+)", base_url)
        if match:
            identifier = match.group(2)
        else:
            if date_str: identifier = date_str.replace("-", "")
            else: identifier = time.strftime("%Y%m%d")
    
    camp = campaign_name.strip() if campaign_name else "CAMPAÑA"
    tracking_param = f"atr_trk=N1-{identifier}-{camp}"
    return f"{base_url}?{tracking_param}"

@app.route("/scraper/download", methods=["POST"])
def scraper_download():
    try:
        total_items = int(request.form.get("total_items", 0))
    except:
        total_items = 0
    
    campaign_name = request.form.get("csv_localizacion", "CAMPAÑA")
    date_str = request.form.get("csv_fenvio", "")

    si = io.StringIO()
    writer = csv.writer(si, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    def trk(u): return inject_tracking(u, campaign_name, date_str)
    
    c = lambda k: request.form.get(k, "")
    e = [""] * 12
    writer.writerow(["LOCALIZACIÓN:", c("csv_localizacion")] + e)
    writer.writerow(["PRODUCTO:", c("csv_producto")] + e)
    writer.writerow(["TIPO DE ENVÍO:", c("csv_tipo_envio")] + e)
    writer.writerow(["FENVIO:", c("csv_fenvio")] + e)
    writer.writerow(["HEADER:", c("csv_header")] + e)
    writer.writerow(["LINK HEADER:", trk(c("csv_link_header"))] + e)
    writer.writerow(["ASUNTO:", c("csv_asunto")] + e)
    writer.writerow(["PREHEADER:", c("csv_preheader")] + e)
    writer.writerow(["TXT_BOTON_FOOTER:", c("csv_txt_boton")] + e)
    writer.writerow(["LINK_FOOTER:", trk(c("csv_link_footer"))] + e)
    writer.writerow(["BANNER_FOOTER:", c("csv_banner")] + e)
    writer.writerow(["LINK_BANNER_FOOTER:", trk(c("csv_link_banner"))] + e)
    writer.writerow(["CONDICIONES_FOOTER:", c("csv_condiciones")] + e)
    writer.writerow([])
    writer.writerow([])
    writer.writerow([])

    writer.writerow(["Orden", "Nombre Oferta", "Metadato 1", "Metadato 2", "Descripción", "URL foto", "URL oferta", "Descuento", "Precio", "Precio ATR", "TAGS", "RATING", "SEPARADOR", "SEPARADOR IMG", "CTA"])
    
    for i in range(1, total_items + 1):
        idx = str(i)
        r_val = request.form.get(f"rating_{idx}", "")
        r_fin = f"{r_val} - Excelente" if r_val and "-" not in r_val else r_val
        
        p_old = force_spanish_format(request.form.get(f"price_old_{idx}", ""))
        p_atr = force_spanish_format(request.form.get(f"price_{idx}", ""))
        
        raw_url = request.form.get(f"url_{idx}")
        tracked_url = inject_tracking(raw_url, campaign_name, date_str)

        writer.writerow([
            request.form.get(f"order_{idx}"),
            request.form.get(f"title_{idx}"),
            request.form.get(f"meta1_{idx}"),
            request.form.get(f"meta2_{idx}"),
            request.form.get(f"desc_{idx}"),
            request.form.get(f"image_{idx}"),
            tracked_url,
            request.form.get(f"discount_{idx}"),
            p_old,
            p_atr,
            request.form.get(f"tag_{idx}", "Sin tag"),
            r_fin,
            request.form.get(f"separator_{idx}", ""),
            "",
            request.form.get(f"cta_{idx}", "Ver plan")
        ])
        
    output = make_response(si.getvalue())
    output.data = si.getvalue().encode('utf-8-sig')
    output.headers["Content-Disposition"] = "attachment; filename=input_scraped.csv"
    # AQUÍ ESTABA EL ERROR, CORREGIDO:
    output.headers["Content-type"] = "text/csv; charset=utf-8-sig"
    output.headers["Content-type"] = "text/csv; charset=utf-8-sig"
    return output


# ============================================================
#   FASE 3: MARKETING TOOLS
# ============================================================

@app.route("/marketing", methods=["GET"])
def marketing_index():
    return render_template("marketing_index.html")

@app.route("/marketing/tracking", methods=["POST"])
def marketing_tracking():
    channel = request.form.get("channel")
    urls_raw = request.form.get("urls", "").strip()
    campaign = request.form.get("campaign", "").strip()
    source = request.form.get("source", "APP") 
    product = request.form.get("product", "Entradas") 
    social_network = request.form.get("social_network", "instagram") 
    format_type = request.form.get("format", "stories") 
    date_str = request.form.get("date_str") 

    urls = [u.strip() for u in urls_raw.splitlines() if u.strip()]
    results = []

    for url in urls:
        final_url = TrackingGenerator.generate_tracking(
            url, channel, campaign, 
            source=source, product=product, 
            social_network=social_network, format=format_type,
            date_str=date_str
        )
        results.append({"original": url, "final": final_url})
    
    return render_template("marketing_result.html", 
                           result_type="Tracking",
                           results=results)

@app.route("/marketing/resize", methods=["POST"])
def marketing_resize():
    urls_raw = request.form.get("urls", "").strip()
    width = request.form.get("width", "")
    quality = request.form.get("quality", "75")
    
    urls = [u.strip() for u in urls_raw.splitlines() if u.strip()]
    results = []

    for url in urls:
        final_url = ImageResizer.resize_atrapalo_url(url, width=width, quality=quality)
        results.append({"original": url, "final": final_url})
    
    return render_template("marketing_result.html", 
                           result_type="Redimensionador CDN",
                           results=results,
                           preview_image=True)


@app.route("/uploads/<path:filename>")
def uploaded_files(filename):
    return send_file(os.path.join(app.config["UPLOAD_FOLDER"], filename))

import webbrowser
from threading import Timer

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    # Configuración de modo debug
    debug_mode = True
    
    # Solo abrir navegador si NO es debug (proceso único) 
    # O si es el proceso hijo del reloader (WERKZEUG_RUN_MAIN = true)
    if not debug_mode or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        Timer(1, open_browser).start()
        
    app.run(debug=debug_mode)