"""
====================================================================
* Author: Minseo Kim
* Purpose: Inspect the DOM of the NLIC origin-based freight page so the
  parser can target labelled cells instead of a positional index.
* Data Source:
    - https://www.nlic.go.kr/nlic/frghtRoad0040.action
* Note:
    Run this once and read the output. It writes the rendered HTML to
    data/raw/_debug_frghtRoad0040_2022_대전.html for offline inspection.
====================================================================
"""

from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager

URL = "https://www.nlic.go.kr/nlic/frghtRoad0040.action"
TARGET_YEAR = "2022"
SAMPLE_REGION = "대전광역시"

raw_dir = Path("data/raw")
raw_dir.mkdir(parents=True, exist_ok=True)

driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))
try:
    driver.get(URL)
    wait = WebDriverWait(driver, 20)

    Select(
        wait.until(EC.presence_of_element_located((By.ID, "S_TOYEAR")))
    ).select_by_value(TARGET_YEAR)
    Select(driver.find_element(By.ID, "S_DEPART_AREA")).select_by_visible_text(
        SAMPLE_REGION
    )
    driver.find_element(By.CSS_SELECTOR, "button.btn-md[type='submit']").click()
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "div.Right_fixed ul.W_110px"))

    html = driver.page_source
finally:
    driver.quit()

(raw_dir / f"_debug_frghtRoad0040_{TARGET_YEAR}_{SAMPLE_REGION}.html").write_text(
    html, encoding="utf-8"
)

soup = BeautifulSoup(html, "html.parser")

print("=== element counts ===")
for sel in (
    "div.Left_fixed li",
    "div.Left_fixed li.con_list",
    "div.Left_fixed li.con_list_1",
    "div.Right_fixed ul.W_110px",
    "div.Right_fixed li.list_sb_1",
    "div.Right_fixed li.list_sb_2",
    "div.Right_fixed li.list_num_01",
    "div.Right_fixed li.list_num_02",
):
    print(f"{len(soup.select(sel)):>6}  {sel}")

print("\n=== row labels (Left_fixed, first 25) ===")
for i, li in enumerate(soup.select("div.Left_fixed li")[:25]):
    text = li.get_text(strip=True)
    if text:
        print(f"[{i:>3}] {text}")

print("\n=== first 3 ul.W_110px, raw HTML ===")
for i, ul in enumerate(soup.select("div.Right_fixed ul.W_110px")[:3]):
    print(f"--- index {i} ---")
    print(ul.prettify()[:400])

print("\n=== index 205-211 text (around the hardcoded 208) ===")
uls = soup.select("div.Right_fixed ul.W_110px")
for i in range(205, min(212, len(uls))):
    print(f"[{i:>3}] {uls[i].get_text(' ', strip=True)!r}")
