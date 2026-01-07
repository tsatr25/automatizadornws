from pathlib import Path
from .renderer import render_newsletter_from_csv


def main():
    # Carpeta base del proyecto
    base_dir = Path(__file__).resolve().parent.parent

    # Aquí pones el nombre del CSV que quieras procesar
    csv_path = base_dir / "data" / "NL OU 2025 - TEST JSON2 (9).csv"

    # Archivo HTML que se va a generar
    output_path = base_dir / "output" / "newsletter.html"

    # Generar HTML
    render_newsletter_from_csv(str(csv_path), str(output_path))

    print("✅ Newsletter generada en:")
    print(output_path)


if __name__ == "__main__":
    main()
