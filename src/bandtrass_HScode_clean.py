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

BASE_DIR = Path(".")
RAW_DIR = BASE_DIR / "data/raw"
PROCESSED_DIR = BASE_DIR / "data/processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def clean_category_name(name):
    """Normalize whitespace and replace spaces with underscores."""
    name = " ".join(str(name).split())
    return name.replace(" ", "_")


def run():
    input_path = RAW_DIR / "codebook_hs_categories_raw.csv"
    output_path = PROCESSED_DIR / "codebook_hs_categories.csv"

    df = pd.read_csv(input_path)

    df["품목약칭_TRASS"] = df["품목약칭_TRASS"].apply(clean_category_name)
    if "HS코드" in df.columns:
        hs_col = df["HS코드"].astype(str).str.strip()
        hs_col = hs_col.str.replace(r"\.0$", "", regex=True)
        hs_col = hs_col.str.zfill(2)
        df["HS코드"] = hs_col
    print(df.head())
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    run()
