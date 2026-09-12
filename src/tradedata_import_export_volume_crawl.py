"""
====================================================================
* Author: Minseo Kim
* Purpose:
    - Crawl regional trade data from the Trade Data Portal
    - Download yearly CSV files for selected comparison regions

* Input:
    - Trade Data Portal:
      https://tradedata.go.kr/cts/index.do#
    - data/processed/codebook_comparison_regions.csv

* Output:
    - data/raw/tradedata_{region}_{year}.csv

* Scope:
    - Regions listed in codebook_comparison_regions.csv
    - Years 2000–2025
    - Regional trade statistics from the "지역별 실적" page

* Notes:
    - Uses Playwright because the site is dynamically rendered.
    - Navigates through "수출입통계" -> "지역별 실적".
    - Selects each target region and year, runs the query, and downloads CSV.
    - DEBUG mode limits the crawl for validation/testing.
====================================================================
"""

from utils_html import get_html
from utils_validate_page import (
    validate_selectors,
    find_hoverable_element,
)
from pathlib import Path
import pandas as pd
import time
from bs4 import BeautifulSoup

BASE_DIR = Path(".")
SAVE_DIR = BASE_DIR / "data/raw"
SAVE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)
INPUT_DIR = BASE_DIR / "data/processed"

url = "https://tradedata.go.kr/cts/index.do#"
regions = pd.read_csv(INPUT_DIR / "codebook_comparison_regions.csv")

TARGET = regions["시도코드"].tolist()
DEBUG = True


def get_selectors(page):
    return {
        "get_by_text": lambda: page.get_by_text(
            "수출입통계",
            exact=True,
        ),
        "div.subTitle": lambda: page.locator(
            "div.subTitle",
            has_text="수출입통계",
        ),
        "text locator": lambda: page.locator('text="수출입통계"'),
    }


def validate_selected_regions(selected_regions, regions):
    selected_df = pd.DataFrame(selected_regions)

    codebook_check = regions[
        regions["시도코드"].astype(str).isin(selected_df["시도코드"])
    ][["시도코드", "시도명"]].copy()

    codebook_check["시도코드"] = codebook_check["시도코드"].astype(str)

    merged = codebook_check.merge(
        selected_df,
        on="시도코드",
        how="outer",
        suffixes=("_codebook", "_selected"),
        indicator=True,
    )
    print(merged)


def action(page):
    selectors = get_selectors(page)
    if DEBUG:
        validate_selectors(selectors)

    menu = find_hoverable_element(selectors, debug=DEBUG)
    menu.hover()

    submenu = page.get_by_title("지역별 실적")

    submenu.wait_for(
        state="visible",
        timeout=5000,
    )
    submenu.click()

    time.sleep(5)

    region_select = page.locator('select[name="sidoCd"]')

    selected_regions = []

    search_button = page.get_by_role("button", name="조회", exact=True)
    print(
        f"\n1) search_button | "
        f"count={search_button.count()} | "
        f"visible={search_button.is_visible()}"
    )
    download_btn = page.locator("button.down_btn")
    print(
        f"\n2) download_btn | "
        f"count={download_btn.count()} | "
        f"visible={download_btn.is_visible()}"
    )

    csv_btn = page.locator("button.downItem.btnCsv")
    print(
        f"\n3) csv_btn | "
        f"count={csv_btn.count()} | "
        f"visible={csv_btn.is_visible()}"
    )

    target_code = TARGET[:1] if DEBUG else TARGET
    for code in target_code:
        region_select.select_option(value=str(code))

        region_name = region_select.locator("option:checked").inner_text()

        selected_regions.append(
            {
                "시도코드": region_select.input_value(),
                "시도명": region_select.locator("option:checked").inner_text(),
            }
        )
        if DEBUG:
            validate_selected_regions(
                selected_regions,
                regions,
            )

        year_select = page.locator('select[name="formYearPc"]')

        target_years = [2000] if DEBUG else range(2000, 2026)

        for year in target_years:
            year_select.select_option(value=str(year))

            time.sleep(3)
            search_button.click()

            time.sleep(3)
            download_btn.click()

            csv_btn.wait_for(
                state="visible",
                timeout=5000,
            )

            target_path = SAVE_DIR / f"tradedata_{region_name}_{year}.csv"
            with page.expect_download() as download_info:
                csv_btn.click()
            download = download_info.value
            download.save_as(target_path)
            print(f"Downloaded: {region_name}/{year} " f"-> {target_path}")


html = get_html(url=url, headless=False, action_callback=action)

soup = BeautifulSoup(html, "html.parser")
