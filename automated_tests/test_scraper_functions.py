import json
import logging
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

# Importing the scraper normally configures a log file as a side effect.
with patch.object(logging, "basicConfig"):
    import iphone_scraper


class PriceParsingTests(unittest.TestCase):
    def test_extracts_price_with_spaces_and_euro_symbol(self):
        self.assertEqual(iphone_scraper.vytiahni_cislo_z_ceny("1 000 €"), 1000)

    def test_extracts_price_without_spaces(self):
        self.assertEqual(iphone_scraper.vytiahni_cislo_z_ceny("480€"), 480)

    def test_returns_none_when_price_is_missing_or_has_no_digits(self):
        self.assertIsNone(iphone_scraper.vytiahni_cislo_z_ceny(None))
        self.assertIsNone(iphone_scraper.vytiahni_cislo_z_ceny("Cena dohodou"))

    def test_accepts_prices_at_configured_boundaries(self):
        config = {"validation": {"min_price": 10, "max_price": 5000}}
        self.assertTrue(iphone_scraper.validate_price(10, config))
        self.assertTrue(iphone_scraper.validate_price(5000, config))
        self.assertFalse(iphone_scraper.validate_price(9, config))
        self.assertFalse(iphone_scraper.validate_price(5001, config))
        self.assertFalse(iphone_scraper.validate_price(None, config))


class DuplicateFilteringTests(unittest.TestCase):
    def test_keeps_first_listing_for_each_exact_product_name(self):
        listings = [
            ("iPhone 15 128GB", "500 €", 500),
            ("iPhone 15 128GB", "450 €", 450),
            ("iPhone 14 128GB", "350 €", 350),
        ]

        self.assertEqual(
            iphone_scraper.remove_duplicates(listings),
            [
                ("iPhone 15 128GB", "500 €", 500),
                ("iPhone 14 128GB", "350 €", 350),
            ],
        )

    def test_does_not_merge_names_that_differ_by_case(self):
        listings = [
            ("iPhone 15", "500 €", 500),
            ("iphone 15", "450 €", 450),
        ]

        self.assertEqual(len(iphone_scraper.remove_duplicates(listings)), 2)


class ConfigurationTests(unittest.TestCase):
    def test_loads_a_valid_config_file(self):
        config = {"search": {"term": "iPhone", "pages": 2}}
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            self.assertEqual(iphone_scraper.load_config(config_path), config)

    def test_missing_config_returns_documented_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "missing.json"

            config = iphone_scraper.load_config(config_path)

        self.assertEqual(config["search"]["term"], "iPhone")
        self.assertEqual(config["search"]["pages"], 10)
        self.assertEqual(config["output"]["delimiter"], ";")

    def test_invalid_json_exits_instead_of_returning_a_fake_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "invalid.json"
            config_path.write_text("{not valid json", encoding="utf-8")

            with self.assertRaises(SystemExit):
                iphone_scraper.load_config(config_path)


if __name__ == "__main__":
    unittest.main()
