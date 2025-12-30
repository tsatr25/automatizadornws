import csv

BADGE_COLORS = {
    "Próximo estreno": "#5631B7",
    "Oferta exclusiva": "#FCC905",
    "Oferta exclusiva Flash": "#FCC905",
    "Novedad": "#027D49",
    "Fecha única": "#96298D",
}

MAX_DESCRIPTION_CHARS = 150


def format_price(value):
    if value is None:
        return None
    try:
        v = float(value)
    except Exception:
        return value

    if v.is_integer():
        return str(int(v))

    return f"{v:.2f}".replace(".", ",")


# ⭐⭐⭐ NUEVO: FORMATEADOR DE RATING ⭐⭐⭐
def format_rating(value):
    """
    - 10.0 → 10
    - 9.5 → 9.5
    - 8 → 8
    - 8.25 → 8.3 (si quieres más precisión te lo ajusto)
    """
    if value is None:
        return None
    try:
        num = float(value)
        if num.is_integer():
            return str(int(num))
        return f"{num:.1f}"
    except:
        return value


def shorten(text: str, max_chars: int = MAX_DESCRIPTION_CHARS) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    truncated = text[: max_chars - 1]
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated + "…"


def parse_header_block(rows):
    header = {}
    footer = {}

    key_map = {
        "HEADER:": ("header", "image_url"),
        "LINK HEADER:": ("header", "link_url"),

        # ⭐ NUEVO → PREHEADER desde CSV
        "PREHEADER:": ("header", "preheader"),
        "\ufeffPREHEADER:": ("header", "preheader"),

        "TXT_BOTON_FOOTER:": ("footer", "button_text"),
        "LINK_FOOTER:": ("footer", "button_url"),
        "BANNER_FOOTER:": ("footer", "banner_image_url"),
        "LINK_BANNER_FOOTER:": ("footer", "banner_link_url"),

        "CONDICIONES_FOOTER:": ("footer", "conditions"),
        "\ufeffCONDICIONES_FOOTER:": ("footer", "conditions"),
    }

    for row in rows:
        if not row or not row[0]:
            continue

        key = row[0].strip()
        value = (row[1] or "").strip() if len(row) > 1 else ""

        target_field = key_map.get(key)
        if not target_field:
            continue

        target, field = target_field
        if target == "header":
            header[field] = value
        elif target == "footer":
            footer[field] = value

    return header, footer


def parse_cards(header_row, data_rows):
    idx = {name: i for i, name in enumerate(header_row)}

    def get(row, name):
        i = idx.get(name)
        if i is None or i >= len(row):
            return ""
        return row[i].strip()

    def to_float(val):
        if not val:
            return None
        val = val.replace(".", "").replace(",", ".")
        try:
            return float(val)
        except ValueError:
            return None

    cards = []

    for row in data_rows:
        if not row or not row[0].strip():
            continue

        try:
            order = int(get(row, "Orden"))
        except ValueError:
            continue

        title = get(row, "Nombre Oferta")
        meta1 = get(row, "Metadato 1")
        meta2 = get(row, "Metadato 2")

        description_raw = get(row, "Descripción")
        description_short = shorten(description_raw)

        image = get(row, "URL foto")
        url = get(row, "URL oferta")

        discount = get(row, "Descuento")
        price_old_raw = get(row, "Precio")
        price_raw = get(row, "Precio ATR")

        tags = get(row, "TAGS")
        separator = get(row, "SEPARADOR")
        separator_img = get(row, "SEPARADOR IMG")

        cta_from_csv = (
            get(row, "CTA")
            or get(row, "\ufeffCTA")
            or get(row, " CTA")
        )

        conditions_raw = get(row, "CONDICIONES")

        # ---------------- RATING ----------------
        rating_raw = get(row, "RATING")
        rating_value = None
        rating_text = None

        if rating_raw:
            if "-" in rating_raw:
                parts = rating_raw.split("-", 1)
                rating_value_str = parts[0].strip().replace(",", ".")
                try:
                    rating_value = float(rating_value_str)
                except Exception:
                    rating_value = None
                rating_text = parts[1].strip()
            else:
                rating_value_str = rating_raw.replace(",", ".")
                try:
                    rating_value = float(rating_value_str)
                except Exception:
                    rating_value = None
                rating_text = None

        price_old_float = to_float(price_old_raw)
        price_float = to_float(price_raw)

        card = {
            "order": order,
            "title": title,
            "metadata_1": meta1,
            "metadata_2": meta2,
            "metadata": f"{meta1.strip()} · {meta2.strip()}".strip(" ·"),

            "description_raw": description_raw,
            "description_short": description_short,
            "description": description_raw,

            "image": image,
            "url": url,

            "cta_url": url,
            "cta_label": cta_from_csv if cta_from_csv else "Ver plan",
            "cta_type": "ver_plan",

            "discount_percentage": int(discount) if discount else None,

            "price_old": format_price(price_old_float) if price_old_float else None,
            "price": format_price(price_float),

            "badge_text": None,
            "badge_color": None,

            # ⭐ RATING REFORMATEADO
            "rating_value": rating_value,
            "rating_value_formatted": format_rating(rating_value) if rating_value is not None else None,
            "rating_text": rating_text,

            "separator": separator or None,
            "separator_image": separator_img or None,

            "conditions": conditions_raw or "",
        }

        if tags and tags.lower() != "sin tag":
            card["badge_text"] = tags
            card["badge_color"] = BADGE_COLORS.get(tags)

        cards.append(card)

    cards.sort(key=lambda c: c["order"])
    return cards


def csv_to_newsletter_dict(csv_path: str) -> dict:
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)

    header_block = []
    table_header = None
    table_rows = []
    in_table = False

    for row in rows:
        if not in_table and row and row[0].strip() == "Orden":
            in_table = True
            table_header = row
            continue

        if not in_table:
            header_block.append(row)
        else:
            table_rows.append(row)

    header, footer = parse_header_block(header_block)

    if table_header is None:
        cards = []
    else:
        cards = parse_cards(table_header, table_rows)

    return {
        "header": header,
        "footer": footer,
        "cards": cards,
    }
