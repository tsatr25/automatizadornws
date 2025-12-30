import requests
from bs4 import BeautifulSoup
import os
import re
import json
import html

# --- CONFIGURACIÓN IA ---
try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key) if api_key else None
except Exception:
    client = None

# --- FUNCIONES AUXILIARES ---

def clean_title_logic(title_raw):
    """Limpia el título de basura SEO."""
    if not title_raw: return ""
    t = title_raw.replace("Entradas para ", "").replace("Entradas ", "")
    if " - " in t:
        parts = t.split(" - ")
        if len(parts[0]) > 5: t = parts[0]
    return t.strip()[:45]

def generate_ai_texts(title_raw, description_raw):
    """Usa IA para resumir. Si falla, corta manualmente."""
    final_title = clean_title_logic(title_raw)
    final_desc = (description_raw[:137] + "...") if description_raw and len(description_raw) > 140 else (description_raw or "")

    if not client:
        return final_title, final_desc

    try:
        system_prompt = (
            "Eres un copywriter experto de Atrápalo. Tu tono es canalla, divertido y directo. "
            "Devuelve un JSON puro con: "
            "1. 'title': <30 chars ideal (max 45). Elimina recintos/ciudades. "
            "2. 'description': Max 140 chars. Invita a la acción."
        )
        user_content = f"TITULO: {title_raw}\nDESC: {description_raw}"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}],
            temperature=0.7,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("title", final_title), data.get("description", final_desc)
    except Exception as e:
        print(f"[IA Error] {e}")
        return final_title, final_desc

def process_image_url(url_raw):
    """Solo acepta CDN de Atrápalo y añade parámetros de recorte."""
    if not url_raw or "cdn.atrapalo.com" not in url_raw:
        return ""
    base_url = url_raw.split("?")[0]
    return f"{base_url}?width=600&height=315&quality=75&auto=avif"

# --- MOTOR DE SCRAPING MEJORADO ---

def get_atrapalo_data(url):
    print(f"⚡ Analizando: {url}")
    try:
        # Cabeceras rotativas para parecer un humano real
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Error Status {response.status_code} - Posible bloqueo.")
            return None

        # Usamos lxml si está disponible, sino html.parser
        try:
            soup = BeautifulSoup(response.content, 'lxml')
        except:
            soup = BeautifulSoup(response.content, 'html.parser')

        data = {'url': url, 'discount': '', 'tag': 'Sin tag', 'rating': '', 'price_old': ''}

        # --- ESTRATEGIA 1: JSON-LD (Datos Estructurados Ocultos) ---
        json_data = {}
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                if not script.string: continue
                js = json.loads(script.string)
                if isinstance(js, dict) and js.get('@type') in ['Product', 'Event']:
                    json_data = js
                    break
                elif isinstance(js, list):
                    for item in js:
                        if item.get('@type') in ['Product', 'Event']:
                            json_data = item
                            break
            except:
                continue

        # --- MAPEO DE DATOS ---

        # 1. TÍTULO Y DESCRIPCIÓN
        raw_title = json_data.get('name') or (soup.find("meta", property="og:title")["content"] if soup.find("meta", property="og:title") else "")
        raw_desc = json_data.get('description') or (soup.find("meta", property="og:description")["content"] if soup.find("meta", property="og:description") else "")
        
        # Decodificar HTML entities
        raw_title = html.unescape(raw_title)
        raw_desc = html.unescape(raw_desc)
        
        # Procesar con IA
        data['title'], data['description'] = generate_ai_texts(raw_title, raw_desc)

        # 2. IMAGEN
        raw_image = json_data.get('image')
        if isinstance(raw_image, list): raw_image = raw_image[0]
        if not raw_image:
            meta_img = soup.find("meta", property="og:image")
            raw_image = meta_img["content"] if meta_img else ""
        
        data['image'] = process_image_url(raw_image)

        # 3. PRECIOS
        offers = json_data.get('offers')
        if isinstance(offers, list): offers = offers[0]
        
        price_json = offers.get('price') if offers else None
        
        if price_json:
            data['price'] = str(price_json)
        else:
            # Fallback a selectores CSS
            price_elem = soup.select_one(".price-amount, .info-price .amount, .price, .a-price")
            data['price'] = price_elem.get_text(strip=True).replace("€", "").replace(",", ".") if price_elem else ""

        # Limpieza precio
        data['price'] = re.sub(r"[^\d\.]", "", data['price'])

        # Precio tachado (viejo)
        old_price_elem = soup.select_one(".price-old, .crossed-out, .a-old-price")
        if old_price_elem:
            data['price_old'] = old_price_elem.get_text(strip=True).replace("€", "").replace(",", ".")
            data['price_old'] = re.sub(r"[^\d\.]", "", data['price_old'])

        # Descuento
        try:
            p_curr = float(data['price'])
            if data['price_old']:
                p_old = float(data['price_old'])
                if p_old > p_curr:
                    data['discount'] = int(((p_old - p_curr) / p_old) * 100)
        except:
            pass

        # 4. UBICACIÓN
        location = json_data.get('location', {})
        venue_name = location.get('name')
        address = location.get('address', {})
        city_name = address.get('addressLocality') if isinstance(address, dict) else None

        if not venue_name:
            loc_elem = soup.select_one(".venue-name, .locality")
            if loc_elem: 
                txt = loc_elem.get_text(strip=True)
                venue_name = txt.split(",")[0].strip() if "," in txt else txt
        
        if not city_name:
            if "madrid" in url: city_name = "Madrid"
            elif "barcelona" in url: city_name = "Barcelona"
            else: city_name = "España"

        data['metadata_1'] = html.unescape(venue_name or "Ubicación")
        data['metadata_2'] = html.unescape(city_name or "")

        # 5. RATING
        agg_rating = json_data.get('aggregateRating', {})
        rating_val = agg_rating.get('ratingValue')
        if rating_val:
            data['rating'] = str(rating_val)
        else:
            rate_elem = soup.select_one(".rating-value, .score")
            if rate_elem: data['rating'] = rate_elem.get_text(strip=True).replace("/10", "")

        # 6. TAGS
        tag_elem = soup.select_one(".product-badge, .label-promotion, .badge-text")
        if tag_elem:
            t = tag_elem.get_text(strip=True).capitalize()
            if len(t) < 25: data['tag'] = html.unescape(t)

        print(f"✅ Éxito: {data['title']}")
        return data

    except Exception as e:
        print(f"❌ CRITICAL ERROR en {url}: {e}")
        return {
            'url': url, 'title': '❌ ERROR LECTURA', 'metadata_1': 'Error', 'metadata_2': 'Error',
            'description': 'No se pudo leer la web. Posible bloqueo.',
            'image': '', 'price': '0', 'discount': '', 'tag': 'Sin tag'
        }