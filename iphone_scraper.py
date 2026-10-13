import csv
import time
import argparse
import sys
import logging
import json
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path='config.json'):
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found, using defaults")
        return {
            'search': {'term': 'iPhone', 'pages': 10},
            'output': {'filename': 'bazos_produkty.csv', 'encoding': 'utf-8-sig', 'delimiter': ';'},
            'scraper': {'delay': 3, 'window_size': '1400,1200', 'headless': False},
            'validation': {'min_price': 10, 'max_price': 5000}
        }
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        sys.exit(1)


def vytvor_driver(config):
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--window-size={config['scraper']['window_size']}")
    options.add_experimental_option("detach", True)
    if config['scraper'].get('headless', False):
        options.add_argument("--headless")
    return webdriver.Chrome(options=options)


def vytiahni_cislo_z_ceny(text_ceny):
    """Extract numeric price from text (e.g., '1 000 €' -> 1000)"""
    if not text_ceny:
        return None
    cisla = "".join(znak for znak in text_ceny if znak.isdigit())
    return int(cisla) if cisla else None


def validate_price(price, config):
    """Validate price is within realistic range."""
    if price is None:
        return False
    min_price = config['validation']['min_price']
    max_price = config['validation']['max_price']
    return min_price <= price <= max_price


def remove_duplicates(listings):
    """Remove duplicate listings based on product name."""
    seen_names = set()
    unique_listings = []
    for nazov, cena_text, cista_cena in listings:
        if nazov not in seen_names:
            seen_names.add(nazov)
            unique_listings.append((nazov, cena_text, cista_cena))
    return unique_listings


def main():
    parser = argparse.ArgumentParser(description='Scrape iPhone listings from Bazos.sk')
    parser.add_argument('--config', default='config.json', help='Config file path (default: config.json)')
    parser.add_argument('--search', help='Override search term from config')
    parser.add_argument('--pages', type=int, help='Override number of pages from config')
    parser.add_argument('--output', help='Override output file from config')
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Override config with command line arguments if provided
    search_term = args.search if args.search else config['search']['term']
    num_pages = args.pages if args.pages else config['search']['pages']
    output_file = args.output if args.output else config['output']['filename']

    logger.info(f"Starting scraper for: {search_term}")
    logger.info(f"Pages to scrape: {num_pages}")
    logger.info(f"Output file: {output_file}")

    driver = None
    base_url = f"https://www.bazos.sk/search.php?hledat={search_term}"
    all_listings = []

    try:
        driver = vytvor_driver(config)

        for posun in range(0, num_pages * 20, 20):
            strana = posun // 20 + 1
            url = f"{base_url}&crz={posun}"
            logger.info(f"Loading page {strana}: {url}")

            try:
                driver.get(url)
                time.sleep(config['scraper']['delay'])
            except WebDriverException as e:
                logger.error(f"Error loading page {strana}: {e}")
                continue

            # Find all listings - links with href containing "inzerat"
            link_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='inzerat']")
            iphone_nazvy = []
            for link in link_elements:
                text = link.text.strip()
                # Only containing search term and not too short
                if search_term.lower() in text.lower() and len(text) > 10:
                    iphone_nazvy.append(text)

            # Find all prices - bold elements with €
            b_elements = driver.find_elements(By.TAG_NAME, "b")
            realne_ceny = []
            for b in b_elements:
                text = b.text.strip()
                # Price must contain € and number, but not be from filter menu
                if "€" in text and any(znak.isdigit() for znak in text) and len(text) < 50:
                    realne_ceny.append(text)

            if not iphone_nazvy:
                logger.warning(f"No listings found on page {strana}.")
                continue

            max_pocet = min(len(iphone_nazvy), len(realne_ceny))

            for i in range(max_pocet):
                nazov = iphone_nazvy[i]
                cena_text = realne_ceny[i]
                cista_cena = vytiahni_cislo_z_ceny(cena_text)

                # Validate price
                if validate_price(cista_cena, config):
                    all_listings.append((nazov, cena_text, cista_cena))
                    logger.info(f"Page {strana} -> {nazov} | Price: {cena_text} | Number: {cista_cena}")
                else:
                    logger.warning(f"Filtered out unrealistic price: {cena_text} for {nazov}")

        # Remove duplicates
        unique_listings = remove_duplicates(all_listings)
        logger.info(f"Total listings found: {len(all_listings)}")
        logger.info(f"After removing duplicates: {len(unique_listings)}")

        # Write to CSV
        with open(output_file, "w", newline="", encoding=config['output']['encoding']) as subor:
            zapisovac = csv.writer(subor, delimiter=config['output']['delimiter'])
            zapisovac.writerow(["Produkt", "Cena", "Čisté číslo"])

            for nazov, cena_text, cista_cena in unique_listings:
                zapisovac.writerow([nazov, cena_text, cista_cena])

        logger.info(f"DONE - All data saved to {output_file}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    main()
