from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .csv_parser import csv_to_newsletter_dict

import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import unicodedata


# ============================================================
#   CONFIG JINJA
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"


def get_jinja_env() -> Environment:
    """
    Configura el entorno Jinja2 para leer plantillas desde /templates.
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env


# ============================================================
#   FUNCIÓN ORIGINAL → Render desde CSV
# ============================================================

def render_newsletter_from_csv(csv_path: str, output_path: str | None = None) -> str:
    """
    - Lee el CSV
    - Genera el diccionario newsletter
    - Renderiza la plantilla HTML con los datos
    - Devuelve el HTML como string
    - Si se pasa output_path, lo guarda como archivo
    """
    data = csv_to_newsletter_dict(csv_path)

    env = get_jinja_env()
    template = env.get_template("newsletter_master.html")

    html = template.render(newsletter=data)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")

    return html


# ============================================================
#   FUNCIÓN → Render desde DICCIONARIO
# ============================================================

def render_newsletter(newsletter_data: dict) -> str:
    """
    Renderiza el newsletter recibiendo un diccionario ya preparado,
    sin necesidad de pasar por la capa CSV.
    """
    env = get_jinja_env()
    template = env.get_template("newsletter_master.html")
    return template.render(newsletter=newsletter_data)


# ============================================================
#   NORMALIZADOR DE CAMPAÑA (UTM)
# ============================================================

def normalize_campaign_name(name: str) -> str:
    """
    Convierte el nombre del newsletter en una campaña UTM limpia:
    - lower case
    - remplaza espacios por guiones
    - quita acentos y caracteres raros
    """
    if not name:
        return "newsletter"

    name = name.strip().lower().replace(" ", "-")

    name = "".join(
        c for c in unicodedata.normalize("NFD", name)
        if unicodedata.category(c) != "Mn"
    )

    return name


# ============================================================
#   INSERTA UTMs SIN ROMPER EL ENLACE ORIGINAL
# ============================================================

def add_utm_params(url: str, campaign: str, content: str) -> str:
    """
    Añade UTMs sin borrar parámetros originales como atr_trk.
    - preserva query existente
    - reemplaza utms preexistentes
    """
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    # UTMs base
    query["utm_source"] = ["atrapalo"]
    query["utm_medium"] = ["newsletter"]
    query["utm_campaign"] = [campaign]
    query["utm_content"] = [content]

    new_query = urlencode(query, doseq=True)

    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))

    return clean_url


# ============================================================
#   APLICA TRACKING UTM A TODO EL HTML
# ============================================================

def apply_utm_tracking(html: str, campaign_name: str) -> str:
    """
    Reemplaza todos los href="..." añadiendo UTMs según su tipo.
    """

    campaign = normalize_campaign_name(campaign_name)

    def replacer(match):
        url = match.group(1)

        # excluir mailto, tel, anclas
        if url.startswith(("mailto:", "tel:", "#")):
            return f'href="{url}"'

        # detectar tipo
        before = match.string[max(0, match.start()-200):match.start()]

        if "single_card_block" in before:
            content = "card"
        elif "hero" in before or "HEADER" in before:
            content = "hero"
        elif "recomendaciones" in before:
            content = "cta-recom"
        elif "banner" in before:
            content = "banner"
        elif "atrapalo-app" in url:
            content = "app"
        elif "houdinis" in url:
            content = "social-houdinis"
        elif "facebook" in url:
            content = "social-facebook"
        elif "instagram" in url:
            content = "social-instagram"
        elif "twitter" in url:
            content = "social-twitter"
        elif "youtube" in url:
            content = "social-youtube"
        elif "atrapalo.com" in url:
            content = "logo"
        else:
            content = "link"

        # añadir utms
        tracked = add_utm_params(url, campaign, content)
        return f'href="{tracked}"'

    return re.sub(r'href="([^"]+)"', replacer, html)
