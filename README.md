# Atrápalo Newsletter Automation Tool

This project is a web-based automation suite designed to streamline the creation, management, and tracking of newsletters for Atrápalo. It includes a smart scraper, a visual editor, and various marketing tools.

## Features

### 1. Visual Editor
- Real-time editing of newsletter blocks.
- Smart alignment of columns and spacers.
- Shareable preview links.
- Persistent archive of edited newsletters.

### 2. Scraper System
- Extract product data (Hotels & Activities) directly from Atrápalo URLs.
- Kanban board for managing draft statuses (Pending, Ready, Archived).
- Bulk price/rating updates with a single click.
- Legacy CSV export for external tool compatibility.

### 3. Marketing Tools
- **Tracking Applicator**: Generate UTM parameters for Push (N27), Social Media (A2), and other channels.
- **Image Resizer**: Leverage Atrápalo's CDN to optimize image weight and dimensions.

## Project Structure

- `src/webapp.py`: Main Flask controller and route definitions.
- `src/scraper.py`: Web scraping logic using BeautifulSoup.
- `src/csv_parser.py`: Logic for parsing and formatting Atrápalo CSV files.
- `src/renderer.py`: HTML generation using Jinja2 templates and UTM injection logic.
- `src/marketing.py`: Shared utilities for tracking and image processing.
- `templates/`: HTML templates for the web interface and the newsletter itself.
- `drafts/`: Persistent storage for scraper drafts (JSON).
- `visual_archives/`: Persistent storage for visual editor newsletters (HTML).

## Installation & Usage

1. **Setup Environment**: Run `setup_env.bat` to create a virtual environment and install dependencies.
2. **Launch**: Use `launch_app.bat` to start the Flask server.
3. **Command Line**: You can use `python -m src.main` to render a newsletter directly from a CSV file without the web interface.

## Developers
This tool is designed to be easily extensible. All core functions are documented with docstrings, and routes are logically sectioned in `webapp.py`.
