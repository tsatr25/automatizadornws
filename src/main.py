"""
CLI Entry Point
Allows generating a newsletter directly from the command line using a local CSV file.
Useful for testing the rendering engine without launching the web server.
"""

from pathlib import Path
from .renderer import render_newsletter_from_csv


def main():
    """Main execution function for CLI-based rendering."""
    base_dir = Path(__file__).resolve().parent.parent
    csv_path = base_dir / "data" / "NL OU 2025 - TEST JSON2 (9).csv"
    output_path = base_dir / "output" / "newsletter.html"
    render_newsletter_from_csv(str(csv_path), str(output_path))

    print("Newsletter generada en:")
    print(output_path)


if __name__ == "__main__":
    main()
