"""
====================================================================
* Author: Minseo Kim
* Purpose: Scrape the inter-regional freight O/D matrix from NLIC.
* Data Source:
    - National Logistics Information Center (NLIC), road freight O/D
    - https://www.nlic.go.kr/nlic/frghtRoad0010.action
* Scope:
    Limited to 2022, the most recent base year of the 전국화물통행실태조사
    (a 5-year cycle national survey). Non-survey years are model estimates
    built on a different baseline, so cross-year comparison is invalid.
* Output:
    - data/raw/nlic_od_matrix_2022.csv   (as scraped, wide)
    - data/processed/nlic_od_long_2022.csv
====================================================================
"""

from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager

URL = "https://www.nlic.go.kr/nlic/frghtRoad0010.action"
TARGET_YEAR = "2022"
DATA_BOX_SELECTOR = "div.box.W_1785px"

raw_dir = Path("data/raw")
processed_dir = Path("data/processed")
raw_dir.mkdir(parents=True, exist_ok=True)
processed_dir.mkdir(parents=True, exist_ok=True)


def parse_volume(text: str) -> int | None:
    """Return the tonnage as int, or None when the cell holds no number.

    Missing cells must not collapse to 0: a zero flow and an unreported flow
    mean different things once the matrix is aggregated.
    """
    cleaned = text.replace(",", "").strip()
    try:
        return int(cleaned)
    except ValueError:
        return None


def find_origins(soup, data_box, expected_rows: int) -> list[str]:
    """Return the row labels, matched by count rather than by position.

    The page renders row headers outside the data box, so the lookup widens
    until a scope yields exactly one label per parsed row. Matching on count
    is what keeps a wider scope from silently pulling in unrelated elements.
    """
    for scope in (data_box, soup):
        labels = [
            li.get_text(strip=True) for li in scope.find_all("li", class_="con_list")
        ]
        if len(labels) == expected_rows:
            return labels
    raise RuntimeError(f"No scope yielded {expected_rows} row labels")


def scrape_matrix(driver) -> pd.DataFrame:
    """Return the O/D matrix with origins as rows and destinations as columns."""
    soup = BeautifulSoup(driver.page_source, "html.parser")
    boxes = soup.select(DATA_BOX_SELECTOR)
    if len(boxes) < 2:
        raise RuntimeError(f"Expected 2 data boxes, found {len(boxes)}")

    header_box, data_box = boxes[0], boxes[1]
    destinations = [ul.get_text(strip=True) for ul in header_box.find_all("ul")]

    matrix, current_row = [], []
    for ul in data_box.find_all("ul"):
        cell = ul.find("li")
        current_row.append(parse_volume(cell.get_text(strip=True)) if cell else None)
        # The last cell of each row carries a right border in its inline style.
        if "border-right" in ul.get("style", ""):
            matrix.append(current_row)
            current_row = []

    if current_row:
        raise RuntimeError(f"Trailing {len(current_row)} cells with no row terminator")

    if not matrix:
        raise RuntimeError("No data rows parsed")
    if len(matrix[0]) != len(destinations):
        raise RuntimeError(
            f"Row width {len(matrix[0])} does not match {len(destinations)} destinations"
        )

    origins = find_origins(soup, data_box, len(matrix))
    df = pd.DataFrame(matrix, index=origins, columns=destinations)
    df.index.name = "출발지"
    df.columns.name = "도착지"
    return df


driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))
try:
    driver.get(URL)
    wait = WebDriverWait(driver, 20)

    Select(
        wait.until(EC.presence_of_element_located((By.ID, "S_TOYEAR")))
    ).select_by_value(TARGET_YEAR)
    driver.find_element(By.CSS_SELECTOR, "button.btn-md[type='submit']").click()
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, DATA_BOX_SELECTOR)) >= 2)

    df_matrix = scrape_matrix(driver)
finally:
    driver.quit()

df_matrix.to_csv(raw_dir / f"nlic_od_matrix_{TARGET_YEAR}.csv", encoding="utf-8-sig")

df_long = df_matrix.stack().rename("물동량").reset_index().assign(연도=int(TARGET_YEAR))
df_long = df_long[["연도", "출발지", "도착지", "물동량"]]
df_long.to_csv(
    processed_dir / f"nlic_od_long_{TARGET_YEAR}.csv", index=False, encoding="utf-8-sig"
)

missing = df_long["물동량"].isna().sum()
print(
    f"{df_matrix.shape[0]}x{df_matrix.shape[1]} matrix | {len(df_long)} pairs | {missing} unparsed"
)
