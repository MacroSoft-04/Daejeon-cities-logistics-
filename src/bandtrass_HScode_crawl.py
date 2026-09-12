"""
====================================================================
* Author: Minseo Kim
* Purpose:
    - Extract HS category codes and descriptions from the Trade Data Portal
    - Save the extracted HS category information as a CSV file

* Input:
    - Trade Data Portal:
      https://www.bandtrass.or.kr/hsnavi.do

* Output:
    - data/raw/hs_categories.csv

* Scope:
    - HS categories available in the Trade Data Portal
    - Extracts the category code and category name displayed in table#sok

* Notes:
    - Uses Playwright because the site is dynamically rendered.
    - Opens the Trade Data Portal in a Chromium browser.
    - Extracts HS category information from table#sok.
    - DEBUG mode is currently defined but not used in the extraction process.
====================================================================
"""

from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright

BASE_DIR = Path(".")
SAVE_DIR = BASE_DIR / "data/raw"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://www.bandtrass.or.kr/hsnavi.do"

DEBUG = True


def extract_hs_codes(page):
    """Extracts HS category codes and descriptions from table#sok."""
    hs_data = []

    page.wait_for_selector("table#sok")

    cells = page.locator("table#sok td.title").all()

    for cell in cells:
        text = cell.inner_text().strip()
        cell_id = cell.get_attribute("id")

        if cell_id and text:
            code_number = cell_id.replace("code", "")
            hs_data.append({"HS코드": code_number, "품목약칭_TRASS": text})
    return pd.DataFrame(hs_data)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto(URL, wait_until="networkidle")

        df_hs = extract_hs_codes(page)
        print("Extracted HS Categories:")
        print(df_hs.head())

        df_hs.to_csv(
            SAVE_DIR / "codebook_hs_categories_raw.csv",
            index=False,
            encoding="utf-8-sig",
        )
        browser.close()


if __name__ == "__main__":
    run()
