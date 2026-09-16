"""
====================================================================
* Author: Minseo Kim
* Purpose:
    - Normalize the crawled HS chapter codebook for joining and labels

* Input:
    - data/raw/codebook_hs_categories_raw.csv

* Output:
    - data/processed/codebook_hs_categories.csv

* Notes:
    - HS코드 stays a zero-padded string; read it back with
      dtype={"HS코드": str} or "01" becomes the integer 1.
====================================================================
"""

from pathlib import Path
import pandas as pd
import re

BASE_DIR = Path(".")
RAW_DIR = BASE_DIR / "data/raw"
PROCESSED_DIR = BASE_DIR / "data/processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

input_path = RAW_DIR / "codebook_hs_categories_raw.csv"
output_path = PROCESSED_DIR / "codebook_hs_categories.csv"

CATEGORY_SEPARATORS = re.compile(r"[\sㆍ·_]+")


def clean_category_name(name) -> str:
    """Collapse whitespace and ㆍ separators into single underscores."""
    return CATEGORY_SEPARATORS.sub("_", str(name).strip())


def run():
    df = pd.read_csv(input_path, encoding="utf-8-sig", dtype={"HS코드": str})
    df["품목약칭_TRASS"] = df["품목약칭_TRASS"].apply(clean_category_name)

    if "HS코드" in df.columns:
        hs_col = df["HS코드"].astype(str).str.strip()
        hs_col = hs_col.str.replace(r"\.0$", "", regex=True)
        hs_col = hs_col.str.zfill(2)
        df["HS코드"] = hs_col
        print(df.sample(10))
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    run()
