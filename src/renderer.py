"""
Renderer Module
Handles HTML generation for newsletters using Jinja2 templates.
Includes utility functions for UTM tracking injection and campaign name normalization.
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .csv_parser import csv_to_newsletter_dict

import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import unicodedata


# Configuration

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


# CSV Rendering

def render_newsletter_from_csv(csv_path: str, output_path: str | None = None) -> str:
    """
    Renders a newsletter directly from a CSV file.
    1. Parses CSV to dictionary.
    2. Renders Jinja2 template.
    3. Saves output if path provided.
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


# Dictionary Rendering

def render_newsletter(newsletter_data: dict) -> str:
    """
    Renders the newsletter using a pre-prepared data dictionary.
    Used by the visual editor and direct JSON flows.
    """
    env = get_jinja_env()
    template = env.get_template("newsletter_master.html")
    return template.render(newsletter=newsletter_data)


# Normalization

def normalize_campaign_name(name: str) -> str:
    """
    Cleans a campaign name for UTM usage.
    Converts to lowercase, removes accents, and replaces spaces with dashes.
    """
    if not name:
        return "newsletter"

    name = name.strip().lower().replace(" ", "-")

    name = "".join(
        c for c in unicodedata.normalize("NFD", name)
        if unicodedata.category(c) != "Mn"
    )

    return name


# UTM Management

def add_utm_params(url: str, campaign: str, content: str) -> str:
    """
    Appends UTM parameters to a URL while preserving existing query parameters.
    Handles 'atr_trk' preservation and prevents duplicate UTMs.
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


# HTML Tracking

def apply_utm_tracking(html: str, campaign_name: str) -> str:
    """
    Parses the entire HTML output and injects UTM tracking into all links.
    Intelligently identifies the 'utm_content' based on the link's context in the HTML.
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

        # añdir utms
        tracked = add_utm_params(url, campaign, content)
        return f'href="{tracked}"'

    return re.sub(r'href="([^"]+)"', replacer, html)
