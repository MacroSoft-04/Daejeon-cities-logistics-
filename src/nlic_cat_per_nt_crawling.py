"""
====================================================================
* Author: Minseo Kim
* Purpose: Scrape road freight volume by commodity and region from NLIC.
* Data Source:
    - National Logistics Information Center (NLIC), road freight statistics
    - https://www.nlic.go.kr/nlic/frghtRoad0020.action
* Scope:
    Limited to 2022, the most recent base year of the 전국화물통행실태조사
    (a 5-year cycle national survey). Non-survey years are model estimates
    built on a different baseline, so cross-year comparison is invalid.
* Source caveat:
    Per the NLIC footnote, from 2013 onward the category labelled 재생재료
    reports 도소매품 figures and 기타 reports 컨테이너 figures. Labels are
    kept as published; rename downstream if the distinction matters.
* Output:
    - data/raw/nlic_commodity_matrix_2022.csv   (as scraped, wide)
    - data/processed/nlic_commodity_long_2022.csv
====================================================================
"""

import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager

URL = "https://www.nlic.go.kr/nlic/frghtRoad0020.action"
TARGET_YEAR = "2022"
COL_SELECTOR = "div.Right_fixed ul.W_320px"

raw_dir = Path("data/raw")
processed_dir = Path("data/processed")
raw_dir.mkdir(parents=True, exist_ok=True)
processed_dir.mkdir(parents=True, exist_ok=True)


def parse_volume(text: str) -> int | None:
    """Return the tonnage as int, or None when the cell holds no number.

    Only separators are stripped. The original regex also removed minus signs
    and decimal points, which would silently corrupt any such value.
    """
    cleaned = re.sub(r"[,\s]", "", text)
    try:
        return int(cleaned)
    except ValueError:
        return None


def parse_headers(soup) -> tuple[list[tuple[str, str]], int]:
    """Return (region, flow_type) column pairs and the count of header blocks."""
    header_uls = [
        ul for ul in soup.select(COL_SELECTOR) if ul.select_one("li.list_sb_1")
    ]
    if not header_uls:
        raise RuntimeError("No region headers found")

    columns = []
    for ul in header_uls:
        region = ul.select_one("li.list_sb_1").get_text(strip=True)
        for span in ul.select("li.list_sb_2 span"):
            flow = span.get_text(strip=True)
            if flow:
                columns.append((region, flow))
    return columns, len(header_uls)


def scrape_matrix(driver) -> pd.DataFrame:
    """Return the commodity x (region, flow) matrix."""
    soup = BeautifulSoup(driver.page_source, "html.parser")

    items = [
        li.get_text(strip=True)
        for li in soup.select("div.Left_fixed li.con_list_1")
        if li.get_text(strip=True)
    ]
    columns, num_blocks = parse_headers(soup)
    data_uls = soup.select(COL_SELECTOR)[num_blocks:]

    matrix = []
    for start in range(0, len(data_uls), num_blocks):
        row = []
        for ul in data_uls[start : start + num_blocks]:
            row.extend(
                parse_volume(span.get_text(strip=True))
                for span in ul.select("li.list_sb_3 span")
            )
        # A short row means the layout shifted; dropping it would hide the break.
        if len(row) != len(columns):
            raise RuntimeError(
                f"Row {len(matrix)} has {len(row)} cells, expected {len(columns)}"
            )
        matrix.append(row)

    if len(matrix) != len(items):
        raise RuntimeError(
            f"Parsed {len(matrix)} rows but found {len(items)} commodity labels"
        )

    df = pd.DataFrame(
        matrix,
        index=pd.Index(items, name="품목"),
        columns=pd.MultiIndex.from_tuples(columns, names=["지역", "구분"]),
    )
    return df


driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))
try:
    driver.get(URL)
    wait = WebDriverWait(driver, 20)

    Select(
        wait.until(EC.presence_of_element_located((By.ID, "S_TOYEAR")))
    ).select_by_value(TARGET_YEAR)
    driver.find_element(By.CSS_SELECTOR, "button.btn-md[type='submit']").click()
    wait.until(
        lambda d: d.find_elements(By.CSS_SELECTOR, "div.Left_fixed li.con_list_1")
    )

    df_matrix = scrape_matrix(driver)
finally:
    driver.quit()

df_matrix.to_csv(
    raw_dir / f"nlic_commodity_matrix_{TARGET_YEAR}.csv", encoding="utf-8-sig"
)

df_long = (
    df_matrix.stack(["지역", "구분"])
    .rename("물동량_톤")
    .reset_index()
    .assign(연도=int(TARGET_YEAR))
)
df_long = df_long[["연도", "품목", "지역", "구분", "물동량_톤"]]
df_long.to_csv(
    processed_dir / f"nlic_commodity_long_{TARGET_YEAR}.csv",
    index=False,
    encoding="utf-8-sig",
)

missing = df_long["물동량_톤"].isna().sum()
print(
    f"{df_matrix.shape[0]} commodities x {df_matrix.shape[1]} columns | "
    f"{len(df_long)} rows | {missing} unparsed"
)
