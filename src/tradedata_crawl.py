"""
====================================================================
* Author: Minseo Kim
* Purpose:
    - Crawl trade data from the Trade Data Portal
* Input:
    - https://tradedata.go.kr/cts/index.do#
* Output:       쓰는 파일
* Scope:        기간·대상·제외 범위와 그 이유
* Notes:        코드만 봐서는 알 수 없는 것
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
from io import StringIO
import sys

BASE_DIR = Path(".")
SAVE_DIR = BASE_DIR / "data/raw"
INPUT_DIR = BASE_DIR / "data/processed"

url = "https://tradedata.go.kr/cts/index.do#"
regions = pd.read_csv(INPUT_DIR / "codebook_comparison_regions.csv")

TARGET = regions["시도코드"]

print(TARGET)

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


def action(page):
    selectors = get_selectors(page)
    if DEBUG:
        validate_selectors(selectors)
        find_hoverable_element(selectors)

    menu = find_hoverable_element(selectors)
    menu.hover()

    submenu = page.get_by_title("지역별 실적")

    submenu.wait_for(
        state="visible",
        timeout=5000,
    )
    submenu.click()

    time.sleep(5)
    print(TARGET)

    for code in TARGET:
        page.select_option("select[name='s_term_gb']", code)


html = get_html(url=url, headless=False, action_callback=action)

soup = BeautifulSoup(html, "html.parser")

buttons = soup.find_all("select_option")
