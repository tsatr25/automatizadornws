"""
Scraper Module
Responsible for extracting product data (Hotels and Activities) from Atrápalo URLs.
Uses BeautifulSoup for parsing and handles different layout patterns.
"""

import requests
from bs4 import BeautifulSoup
import json
import re


def get_atrapalo_data(url):
    """
    Main entry point for scraping a URL.
    Identifies the product type (Hotel vs Activity) and calls the appropriate parser.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        if "/hoteles/" in url:
            return parse_hotel(soup, url)
        else:
            return parse_activity(soup, url)

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def parse_activity(soup, url):
    """
    Parses 'Ocio Urbano' (Activities) pages.
    Extracts title, location (metadata), images, base price, and ratings.
    """
    data = {
        'url': url,
        'title': '', 'description': '', 'image': '',
        'price': '', 'price_old': '', 'discount': '',
        'metadata_1': '', 'metadata_2': '', 'rating': '', 'tag': 'Sin tag',
        'cta': 'Ver plan', 'separator': ''
    }

    # Título
    try:
        h1 = soup.find('h1')
        if h1: data['title'] = h1.get_text(strip=True)
    except: pass

    # Metadatos (Recinto y Ciudad)
    try:
        loc_div = soup.select_one('.c-header-product__location, .product-location')
        if loc_div:
            parts = [span.get_text(strip=True) for span in loc_div.find_all(['a', 'span'])]
            parts = [p for p in parts if p and "," not in p]
            if len(parts) > 0: data['metadata_2'] = parts[-1] # Ciudad
            if len(parts) > 1: data['metadata_1'] = parts[0] # Recinto
    except: pass

    # Imagen
    try:
        og_img = soup.find("meta", property="og:image")
        if og_img: data['image'] = og_img["content"]
    except: pass

    # Precio
    try:
        price_meta = soup.select_one('.product-price__value, .c-price-box__amount')
        if price_meta:
            data['price'] = price_meta.get_text(strip=True).replace("€", "").replace("desde", "").strip()
    except: pass

    # Descripción
    try:
        desc_div = soup.select_one('.product-description__content, .c-read-more__content')
        if desc_div:
            text = desc_div.get_text(" ", strip=True)
            data['description'] = text[:160] + "..."
    except: pass
    
    # Rating
    try:
        rate_box = soup.select_one('.rating-value, .c-rating-badge__score')
        if rate_box:
            data['rating'] = rate_box.get_text(strip=True).replace("/10", "")
    except: pass

    return data

def parse_hotel(soup, url):
    """
    Parses Hotel pages with specific logic for stars, city extraction, and tags.
    Handles JSON-LD script parsing for robust price extraction.
    """
    data = {
        'url': url,
        'title': '', 
        'description': '', 
        'image': '',
        'price': '', 
        'price_old': '', 
        'discount': '',
        'metadata_1': 'Hotel 3* en hab. doble',
        'metadata_2': '', # SIEMPRE VACÍO
        'rating': '', 
        'tag': 'Sin tag',
        'cta': 'Ver hotel',
        'separator': ''
    }

    # TITLE
    try:
        h1 = soup.select_one('h1.detail-header__title, h1')
        if h1: data['title'] = h1.get_text(strip=True)
    except: pass

    # CITY
    city = "tu destino"
    try:
        addr = soup.select_one('.detail-header__address, .address')
        if addr:
            full_addr = addr.get_text(strip=True)
            if "," in full_addr:
                city = full_addr.split(",")[-1].strip()
    except: pass

    # ESTRELLAS
    stars = "3"
    try:
        star_icons = soup.select('.icon-star, .stars i, .category-stars i')
        if star_icons:
            stars = str(len(star_icons))
        else:
            text_content = soup.get_text().lower()
            if "5 estrellas" in text_content: stars = "5"
            elif "4 estrellas" in text_content: stars = "4"
            elif "2 estrellas" in text_content: stars = "2"
    except: pass
    
    data['metadata_1'] = f"Hotel {stars}* en hab. doble"

    # IMAGE
    try:
        og_img = soup.find("meta", property="og:image")
        if og_img: data['image'] = og_img["content"]
    except: pass

    # PRICE
    try:
        # JSON-LD
        scripts = soup.find_all('script', type='application/ld+json')
        found_price = False
        for s in scripts:
            if 'priceRange' in s.text:
                js = json.loads(s.text)
                if 'priceRange' in js:
                    data['price'] = js['priceRange'].replace("€", "").strip()
                    found_price = True
                    break
        
        # Meta Price
        if not found_price:
            meta_price = soup.find("meta", property="product:price:amount")
            if meta_price: data['price'] = meta_price["content"]
    except: pass

    # DESCRIPTION
    try:
        desc = soup.find("meta", attrs={"name": "description"})
        raw_text = ""
        if desc: 
            raw_text = desc["content"]
        else:
            body_desc = soup.select_one('.description, .hotel-description')
            if body_desc: raw_text = body_desc.get_text(strip=True)
        
        if raw_text:
            raw_text = raw_text.replace("Reserva ahora en", "").replace("al mejor precio", "")
            if not raw_text.lower().startswith(f"en {city.lower()}"):
                final_desc = f"En {city}, {raw_text}"
            else:
                final_desc = raw_text
                
            if len(final_desc) > 150:
                final_desc = final_desc[:147].rsplit(' ', 1)[0] + "..."
            
            data['description'] = final_desc
    except: pass

    # RATING
    try:
        score = soup.select_one('.badge-rating__score, .rating-score')
        if score: data['rating'] = score.get_text(strip=True)
    except: pass

    # TAGS
    try:
        body_text = soup.get_text().lower()
        found_tags = []

        # Palabras clave prioritarias
        if "pistas" in body_text or "esquí" in body_text: found_tags.append("A pie de pistas")
        if "spa" in body_text or "wellness" in body_text: found_tags.append("Spa")
        if "desayuno incluido" in body_text or "régimen: desayuno" in body_text: found_tags.append("Con Desayuno")
        elif "desayuno" in body_text: found_tags.append("Desayuno")
        
        if not found_tags and "piscina" in body_text: found_tags.append("Piscina")
        
        if found_tags:
            data['tag'] = " / ".join(found_tags[:1])
    except: pass

    return data