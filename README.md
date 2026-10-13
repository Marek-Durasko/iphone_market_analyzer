# iPhone Scraper - Bazos.sk

A web scraper that extracts iPhone listings from Bazos.sk (Slovak classifieds site) and saves them to a CSV file.

## Features

- Scrapes iPhone listings from multiple pages
- Extracts product name, price, and numeric price value
- Saves data to CSV with UTF-8 BOM encoding (Excel compatible)
- Configurable number of pages to scrape
- Includes automated unit tests and a live Bazos.sk end-to-end (E2E) test

## System Requirements

- Python 3.7+
- Chrome browser (must be installed)

## Python Dependencies

- Selenium 4.0+
- Pandas 2.0+
- Matplotlib 3.7+

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure Chrome browser is installed on your system.

## Usage

Basic usage (scrapes 10 pages of iPhone listings):
```bash
python iphone_scraper.py
```

With custom options:
```bash
python iphone_scraper.py --search "Samsung" --pages 5 --output samsung_products.csv
```

### Command Line Arguments

- `--search`: Search term (default: iPhone)
- `--pages`: Number of pages to scrape (default: 10)
- `--output`: Output CSV filename (default: bazos_produkty.csv)

### Examples

Scrape Samsung phones:
```bash
python iphone_scraper.py --search "Samsung" --pages 5
```

Scrape 20 pages of iPhones:
```bash
python iphone_scraper.py --search "iPhone" --pages 20
```

Custom output file:
```bash
python iphone_scraper.py --output my_data.csv
```

## Output

The script creates a CSV file with the following columns:
- **Produkt**: Product title (the original Slovak CSV header)
- **Cena**: Price as displayed on the site (the original Slovak CSV header)
- **Čisté číslo**: Numeric price value for sorting and calculations (the
  original Slovak CSV header)

## Configuration

The script can be configured via:

1. **Config file** (`config.json`) - Recommended for most settings
2. **Command line arguments** - Override config file settings

### Config File (config.json)

```json
{
  "search": {
    "term": "iPhone",
    "pages": 10
  },
  "output": {
    "filename": "bazos_produkty.csv",
    "encoding": "utf-8-sig",
    "delimiter": ";"
  },
  "scraper": {
    "delay": 3,
    "window_size": "1400,1200",
    "headless": false
  },
  "validation": {
    "min_price": 10,
    "max_price": 5000
  }
}
```

### Features

- **Logging**: All operations are logged to `scraper.log` and console
- **Duplicate filtering**: Automatically removes duplicate listings
- **Price validation**: Filters out unrealistic prices (configurable range)
- **Configurable**: Easy to modify search terms, pages, and validation rules

## Data Analysis & Visualization

After scraping, you can analyze the data with the included analysis script:

```bash
python analyze.py
```

This will:
- Calculate statistics (average, median, min, max prices)
- Show distribution by iPhone model
- Generate 3 visualization charts in the `charts/` directory:
  - Price distribution histogram
  - Average price by model (bar chart)
  - Number of listings by model (bar chart)

### Analysis Options

```bash
# Use custom input file
python analyze.py --input my_data.csv

# Save charts to custom directory
python analyze.py --output-dir my_charts
```

## Interactive Dashboard

Generate a standalone dashboard from the project folder:

```powershell
.\.venv\Scripts\python.exe dashboard.py
```

This creates `dashboard.html` and opens it in your browser. The dashboard
includes interactive model and price filters, summary metrics, charts, a
listing table, and a button to download filtered listings as CSV. It works
offline and does not require an additional package.

Use another CSV or choose an output file with:

```powershell
.\.venv\Scripts\python.exe dashboard.py --input my_data.csv --output my_dashboard.html
```

## Automated Tests

The `automated_tests/` folder contains local unit tests and a live
end-to-end (E2E) test for the Bazos.sk search flow.

### Local Unit Tests

The unit tests cover price parsing, configured price limits, duplicate
removal, and configuration loading. They do not require an internet
connection or Chrome.

Run them from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s automated_tests -p "test_scraper_functions.py" -v
```

### Live Bazos.sk End-to-End (E2E) Test

This automated browser test exercises the complete search flow against the
live website: it loads Bazos.sk, enters "iPhone" in the search field, submits
the search, and verifies that matching listings appear. It requires Chrome
and an internet connection, and depends on the website's availability and
current page structure.

The test is opt-in. Run it from the project root in PowerShell:

```powershell
$env:RUN_LIVE_BAZOS = "1"
.\.venv\Scripts\python.exe -m unittest discover -s automated_tests -p "test_live_bazos.py" -v
Remove-Item Env:RUN_LIVE_BAZOS
```

Without `RUN_LIVE_BAZOS=1`, the live test is skipped so routine local test
runs do not fail when the website is unavailable.

## Notes

- The script uses Selenium with Chrome in graphical mode (headless: false in config.json)
- Each page load has a 3-second delay to be respectful to the server
- The browser window stays open after scraping (detach: True) for debugging
- You can change headless to true in config.json to run the browser in the background

## Troubleshooting

If you see `ModuleNotFoundError: No module named 'selenium'`:
```bash
pip install selenium
```

If Chrome fails to launch, make sure Chrome browser is installed on your system.
