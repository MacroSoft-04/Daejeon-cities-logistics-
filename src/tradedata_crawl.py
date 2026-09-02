from pathlib import Path
import pandas as pd
from utils_html import get_html
import time
from bs4 import BeautifulSoup
from io import StringIO


def action(page):
    page.get_by_text("수출입통계")
    page.get_by_text("지역별 실적")


html = get_html(
    url="https://tradedata.go.kr/cts/index.do#",
    headless=False,
)

soup = BeautifulSoup(html, "html.parser")
buttons = soup.find_all("button")
target = soup.find(
    lambda tag: tag.name in ["button", "a", "div", "span"]
    and "수출입통계" in tag.get_text(strip=True)
)

print(target)
