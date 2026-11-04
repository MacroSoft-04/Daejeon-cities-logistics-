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
SAVE_DIR = BASE_DIR / "data/raw/trade_data"
SAVE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

url = "https://tradedata.go.kr/cts/index.do#"

DEBUG = False


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


def validate_selected_regions(selected_regions):
    selected_df = pd.DataFrame(selected_regions)

    codebook_check = selected_regions[
        selected_regions["시도코드"].astype(str).isin(selected_df["시도코드"])
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

    region_select = page.locator('select[name="sidoCd"]')

    for option in region_select.locator("option").all():
        print(option.get_attribute("value"), option.inner_text().strip())

    target_regions = [
        {
            "시도코드": option.get_attribute("value"),
            "시도명": option.inner_text().strip(),
        }
        for option in region_select.locator("option").all()
    ]

    for region in target_regions:
        region_select.select_option(value=region["시도코드"])

        year_select = page.locator('select[name="formYearPc"]')

        target_years = [2000] if DEBUG else range(2000, 2026)

        for year in target_years:
            SAVE_PATH = SAVE_DIR / f"tradedata_{region['시도명']}_{year}.csv"

            if SAVE_PATH.exists():
                print(f"File already exists: {SAVE_PATH}. Skipping.")
                continue

            year_select.select_option(value=str(year))
            search_button.click()
            time.sleep(3)
            print(f"\nClicking download button for {region['시도명']} {year}.")
            print(
                f"Download button visible: {download_btn.is_visible()}|count={download_btn.count()}"
            )
            print(f"CSV button visible: {csv_btn.is_visible()}|count={csv_btn.count()}")

            download_btn.click()
            time.sleep(2)
            print(
                f"CSV button visible after download click: {csv_btn.is_visible()}|count={csv_btn.count()}"
            )
            print(
                f"Download button HTML: {download_btn.evaluate("el => el.outerHTML")}"
            )
            print(f"CSV button HTML: {csv_btn.evaluate("el => el.outerHTML")}")

            failed_files = []

            if not csv_btn.is_visible():
                print(
                    f"CSV button not visible for {region['시도명']} {year}. Skipping."
                )
                failed_files.append(f"{region['시도명']}_{year}")
                continue
            try:
                with page.expect_download(timeout=15000) as download_info:
                    csv_btn.click()
                download = download_info.value
                download.save_as(SAVE_PATH)
                print(f"Downloaded: {region['시도명']}/{year} " f"-> {SAVE_PATH}")
                continue

            except Exception as e:
                print(f"Download failed for {region['시도명']} {year}: {e}")
                print(f"current page URL: {page.url}")
                failed_files.append(f"{region['시도명']}_{year}")
                continue
    if failed_files:
        print(f"\nFailed downloads for the following files: {failed_files}")
    else:
        print("\nAll downloads completed successfully.")


def crawl_trade_data():
    """Crawl trade data for all regions and years."""
    html = get_html(url=url, headless=False, action_callback=action)
    soup = BeautifulSoup(html, "html.parser")
    print(soup.title)


def validate_crawl_results():
    """Validate downloaded CSV files and summarize successful downloads."""
    successful_download = []

    csv_files = list(SAVE_DIR.glob(f"tradedata_*.csv"))
    if not csv_files:
        print("No CSV files found in the save directory.")
        return
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            if df.empty:
                print(f"Warning: {csv_file} is empty.")
                continue

            stem = csv_file.stem
            region_name, year = stem.removeprefix("tradedata_").rsplit("_", 1)
            year = int(year)
            successful_download.append(
                {"시도명": region_name, "연도": year, "file": csv_file}
            )
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
    if not successful_download:
        print("No successful downloads found.")
        return

    successful_df = pd.DataFrame(successful_download)
    ranges = (
        successful_df.groupby("시도명")["연도"]
        .agg(["min", "max", "count"])
        .rename(columns={"min": "Start Year", "max": "End Year", "count": "Count"})
    )
    print("\nSummary of successful downloads:")
    print(ranges.to_string())
    return successful_df


if __name__ == "__main__":
    validate_crawl_results()
