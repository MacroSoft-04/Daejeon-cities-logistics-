"""
====================================================================
* Author: Minseo Kim
* Purpose: Scrape the origin x destination x commodity freight matrix
  from NLIC, one origin region per query.
* Data Source:
    - https://www.nlic.go.kr/nlic/frghtRoad0040.action
* Scope:
    Limited to 2022, the most recent base year of the 전국화물통행실태조사
    (a 5-year cycle national survey). Non-survey years are model estimates
    built on a different baseline, so cross-year comparison is invalid.
* Layout:
    Per query the grid is 17 destinations x 32 commodity columns. The first
    32 ul.W_110px blocks are the commodity headers; the remaining 544 are
    the values in row-major order.
* Output:
    - data/processed/nlic_od_commodity_2022.csv
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

URL = "https://www.nlic.go.kr/nlic/frghtRoad0040.action"
TARGET_YEAR = "2022"
CELL_SELECTOR = "div.Right_fixed ul.W_110px"
TOTAL_COLUMN = "합계"

processed_dir = Path("data/processed")
processed_dir.mkdir(parents=True, exist_ok=True)


def parse_volume(text: str) -> int | None:
    """Return the tonnage as int, or None when the cell holds no number."""
    cleaned = re.sub(r"[,\s]", "", text)
    try:
        return int(cleaned)
    except ValueError:
        return None


def parse_grid(html: str) -> pd.DataFrame:
    """Return one origin's destination x commodity grid."""
    soup = BeautifulSoup(html, "html.parser")

    # The first Left_fixed entry is the "도착지" column caption, not a region.
    destinations = [li.get_text(strip=True) for li in soup.select("div.Left_fixed li")][
        1:
    ]
    commodities = [
        ul.get_text(strip=True)
        for ul in soup.select(CELL_SELECTOR)
        if ul.select_one("li.list_sb_4")
    ]

    cells = [
        ul for ul in soup.select(CELL_SELECTOR) if not ul.select_one("li.list_sb_4")
    ]
    expected = len(destinations) * len(commodities)
    if len(cells) != expected:
        raise RuntimeError(
            f"Got {len(cells)} value cells, expected {len(destinations)}x{len(commodities)}={expected}"
        )

    values = [parse_volume(ul.get_text(strip=True)) for ul in cells]
    rows = [
        values[i : i + len(commodities)]
        for i in range(0, len(values), len(commodities))
    ]

    return pd.DataFrame(
        rows,
        index=pd.Index(destinations, name="도착지"),
        columns=pd.Index(commodities, name="품목"),
    )


def check_totals(grid: pd.DataFrame, origin: str) -> None:
    """Warn when the published 합계 column disagrees with the item columns.

    A mismatch means the column split is wrong or a cell failed to parse, and
    it would otherwise stay invisible until the aggregate numbers are used.
    """
    if TOTAL_COLUMN not in grid.columns:
        return
    parts = grid.drop(columns=TOTAL_COLUMN).sum(axis=1)
    diff = (grid[TOTAL_COLUMN] - parts).abs()
    worst = diff.max()
    if worst > 0:
        print(f"  ! {origin}: 합계 mismatch, max diff {worst:,} at {diff.idxmax()}")


driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))
frames = []
try:
    driver.get(URL)
    wait = WebDriverWait(driver, 30)

    year_select = Select(
        wait.until(EC.presence_of_element_located((By.ID, "S_TOYEAR")))
    )
    year_select.select_by_value(TARGET_YEAR)

    # Read origins from the dropdown so a change in region naming cannot
    # silently drop a region the way a hardcoded list would.
    origins = [
        opt.text.strip()
        for opt in Select(driver.find_element(By.ID, "S_DEPART_AREA")).options
        if opt.get_attribute("value")
    ]
    print(f"{len(origins)} origin regions found")

    for origin in origins:
        Select(driver.find_element(By.ID, "S_TOYEAR")).select_by_value(TARGET_YEAR)
        Select(driver.find_element(By.ID, "S_DEPART_AREA")).select_by_visible_text(
            origin
        )

        stale_marker = driver.find_elements(By.CSS_SELECTOR, CELL_SELECTOR)
        driver.find_element(By.CSS_SELECTOR, "button.btn-md[type='submit']").click()

        # Without this the next parse can silently re-read the previous region.
        if stale_marker:
            wait.until(EC.staleness_of(stale_marker[0]))
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, CELL_SELECTOR)) > 0)

        grid = parse_grid(driver.page_source)
        check_totals(grid, origin)

        frames.append(
            grid.stack()
            .rename("물동량_톤")
            .reset_index()
            .assign(출발지=origin, 연도=int(TARGET_YEAR))
        )
        print(f"  {origin}: {grid.shape[0]}x{grid.shape[1]}")
finally:
    driver.quit()

df_long = pd.concat(frames, ignore_index=True)[
    ["연도", "출발지", "도착지", "품목", "물동량_톤"]
]
out_path = processed_dir / f"nlic_od_commodity_{TARGET_YEAR}.csv"
df_long.to_csv(out_path, index=False, encoding="utf-8-sig")

missing = df_long["물동량_톤"].isna().sum()
print(f"\n{len(df_long):,} rows | {missing} unparsed | saved to {out_path}")
