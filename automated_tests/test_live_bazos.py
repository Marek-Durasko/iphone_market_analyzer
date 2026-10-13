import os
import unittest
from urllib.parse import parse_qs, urlparse

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import WebDriverWait


class BazosLiveSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("RUN_LIVE_BAZOS") != "1":
            raise unittest.SkipTest(
                "Live website test is opt-in; set RUN_LIVE_BAZOS=1 to run it."
            )

        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1400,1200")
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.set_page_load_timeout(30)
        cls.wait = WebDriverWait(cls.driver, 20)

    @classmethod
    def tearDownClass(cls):
        driver = getattr(cls, "driver", None)
        if driver is not None:
            driver.quit()

    def test_homepage_search_field_and_iphone_results(self):
        self.driver.get("https://www.bazos.sk/")
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        self.assertIn(
            "bazos.sk",
            urlparse(self.driver.current_url).netloc.lower(),
            "Bazos.sk did not finish loading at its expected address.",
        )

        try:
            search_field = self.wait.until(
                expected.visibility_of_element_located((By.NAME, "hledat"))
            )
        except TimeoutException:
            self.fail("The Bazos.sk search field (name='hledat') did not appear.")

        self.assertTrue(search_field.is_enabled(), "The search field is disabled.")
        search_field.clear()
        search_field.send_keys("iPhone")
        search_field.send_keys(Keys.ENTER)

        try:
            self.wait.until(
                lambda driver: parse_qs(urlparse(driver.current_url).query)
                .get("hledat", [""])[0]
                .casefold()
                == "iphone"
            )
        except TimeoutException:
            self.fail("Submitting the search field did not start an iPhone search.")

        try:
            self.wait.until(
                lambda driver: any(
                    "iphone" in link.text.casefold()
                    for link in driver.find_elements(
                        By.CSS_SELECTOR, "a[href*='inzerat']"
                    )
                    if len(link.text.strip()) > 10
                )
            )
        except TimeoutException:
            self.fail("The iPhone search returned no listing titles containing 'iPhone'.")

        results = [
            link.text.strip()
            for link in self.driver.find_elements(By.CSS_SELECTOR, "a[href*='inzerat']")
            if "iphone" in link.text.casefold() and len(link.text.strip()) > 10
        ]
        self.assertTrue(
            results,
            "Search completed, but no listing title contains the word 'iPhone'.",
        )


if __name__ == "__main__":
    unittest.main()
