import requests
from bs4 import BeautifulSoup
import json
import re

def get_atrapalo_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # DETECTOR INTELIGENTE
        if "/hoteles/" in url:
            return parse_hotel(soup, url)
        else:
            return parse_activity(soup, url)

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def parse_activity(soup, url):
    """Lógica estándar para Ocio Urbano"""
    data = {
        'url': url,
        'title': '', 'description': '', 'image': '',
        'price': '', 'price_old': '', 'discount': '',
        'metadata_1': '', 'metadata_2': '', 'rating': '', 'tag': 'Sin tag',
        'cta': 'Ver plan', 'separator': ''
    }

    try:
        h1 = soup.find('h1')
        if h1: data['title'] = h1.get_text(strip=True)
    except: pass

    try:
        loc_div = soup.select_one('.c-header-product__location, .product-location')
        if loc_div:
            parts = [span.get_text(strip=True) for span in loc_div.find_all(['a', 'span'])]
            parts = [p for p in parts if p and "," not in p]
            if len(parts) > 0: data['metadata_2'] = parts[-1] # Ciudad
            if len(parts) > 1: data['metadata_1'] = parts[0] # Recinto
    except: pass

    try:
        og_img = soup.find("meta", property="og:image")
        if og_img: data['image'] = og_img["content"]
    except: pass

    try:
        price_meta = soup.select_one('.product-price__value, .c-price-box__amount')
        if price_meta:
            data['price'] = price_meta.get_text(strip=True).replace("€", "").replace("desde", "").strip()
    except: pass

    try:
        desc_div = soup.select_one('.product-description__content, .c-read-more__content')
        if desc_div:
            # Limpieza básica IA simulada
            text = desc_div.get_text(" ", strip=True)
            data['description'] = text[:160] + "..."
    except: pass
    
    try:
        rate_box = soup.select_one('.rating-value, .c-rating-badge__score')
        if rate_box:
            data['rating'] = rate_box.get_text(strip=True).replace("/10", "")
    except: pass

    return data

def parse_hotel(soup, url):
    """Lógica específica para HOTELES (Reglas estrictas)"""
    data = {
        'url': url,
        'title': '', 
        'description': '', 
        'image': '',
        'price': '', 
        'price_old': '', 
        'discount': '',
        'metadata_1': 'Hotel 3* en hab. doble', # Default
        'metadata_2': '', # SIEMPRE VACÍO
        'rating': '', 
        'tag': 'Sin tag', # SIEMPRE SIN TAG
        'cta': 'Ver hotel', # CTA ESPECÍFICO
        'separator': ''
    }

    # 1. TÍTULO
    try:
        h1 = soup.select_one('h1.detail-header__title, h1')
        if h1: data['title'] = h1.get_text(strip=True)
    except: pass

    # 2. CIUDAD (Para usar en la descripción, NO en el metadato)
    city = "tu destino"
    try:
        addr = soup.select_one('.detail-header__address, .address')
        if addr:
            full_addr = addr.get_text(strip=True)
            if "," in full_addr:
                city = full_addr.split(",")[-1].strip() # Sacamos la ciudad
    except: pass

    # 3. ESTRELLAS (Para construir el Meta 1)
    stars = "3" # Default
    try:
        # Buscamos iconos de estrellas o clases específicas
        star_icons = soup.select('.icon-star, .stars i, .category-stars i')
        if star_icons:
            stars = str(len(star_icons))
        else:
            # Fallback: Buscar texto "4 estrellas"
            text_content = soup.get_text().lower()
            if "5 estrellas" in text_content: stars = "5"
            elif "4 estrellas" in text_content: stars = "4"
            elif "2 estrellas" in text_content: stars = "2"
    except: pass
    
    # REGLA: "Hotel X* en hab. doble"
    data['metadata_1'] = f"Hotel {stars}* en hab. doble"

    # 4. IMAGEN
    try:
        og_img = soup.find("meta", property="og:image")
        if og_img: data['image'] = og_img["content"]
    except: pass

    # 5. PRECIO (Desde JSON-LD)
    try:
        scripts = soup.find_all('script', type='application/ld+json')
        for s in scripts:
            if 'priceRange' in s.text:
                js = json.loads(s.text)
                if 'priceRange' in js:
                    data['price'] = js['priceRange'].replace("€", "").strip()
                    break
    except: pass

    # 6. DESCRIPCIÓN (Lógica "IA" simulada: Ciudad + Texto corto)
    try:
        desc = soup.find("meta", attrs={"name": "description"})
        raw_text = ""
        if desc: 
            raw_text = desc["content"]
        else:
            # Fallback al cuerpo
            body_desc = soup.select_one('.description, .hotel-description')
            if body_desc: raw_text = body_desc.get_text(strip=True)
        
        # Limpieza y formateo tono marca
        if raw_text:
            # Quitamos frases comunes de SEO si las hay
            raw_text = raw_text.replace("Reserva ahora en", "").replace("al mejor precio", "")
            
            # Construimos la frase: "En {Ciudad}..."
            if city.lower() not in raw_text.lower():
                final_desc = f"En {city}, {raw_text}"
            else:
                final_desc = raw_text
                
            # Cortamos a 150 caracteres aprox respetando palabras
            if len(final_desc) > 150:
                final_desc = final_desc[:147].rsplit(' ', 1)[0] + "..."
            
            data['description'] = final_desc
    except: pass

    # 7. RATING
    try:
        score = soup.select_one('.badge-rating__score, .rating-score')
        if score: data['rating'] = score.get_text(strip=True)
    except: pass

    return data