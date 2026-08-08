"""
====================================================================
* Author: Minseo Kim
* Data Sources:
    - Deajeon Metropolitan City Trends in Building Construction Starts Area(2020~2025)
    - 2021년 12월 착공 통계 세부내역: http://viewer.daejeon.go.kr:8080/SynapDocViewServer/viewer/doc.html?key=20ecaec9b07f4978ab15f94b907ef94c&convType=html&convLocale=ko_KR&contextPath=/SynapDocViewServer/
    - 2023년 12월 착공 통계 세부내역: http://viewer.daejeon.go.kr:8080/SynapDocViewServer/viewer/doc.html?key=beb02fb4c673425ba0c206e48cc34c5c&convType=html&convLocale=ko_KR&contextPath=/SynapDocViewServer/
    - 2025년 12월 착공 통계 세부내역: http://viewer.daejeon.go.kr:8080/SynapDocViewServer/viewer/doc.html?key=c8913ff8727240b981e4841d2ad4ecc2&convType=html&convLocale=ko_KR&contextPath=/SynapDocViewServer/
* Crawling
* Output: data/dmc_dj_const_2020_2025.csv
====================================================================
"""

import re
import traceback
from pathlib import Path
from typing import Tuple

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def scrape_with_selenium(
    target_url: str, default_years: Tuple[int, int]
) -> pd.DataFrame:
    """Selenium으로 사이냅 뷰어를 동적 렌더링한 후 건축 착공 누계 데이터 추출"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(target_url)
        wait = WebDriverWait(driver, 30)

        # 1. iframe switch
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "innerWrap")))

        # 2. Wait for rows to load
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.tr")) > 0)

        # 3. Collect all row elements
        rows = driver.find_elements(By.CSS_SELECTOR, "div.tr")

        year_1, year_2 = default_years

        # --- STEP 1: Dynamic Year Header Detection ---
        for row in rows:
            tds = row.find_elements(By.CSS_SELECTOR, "div[class*='td']")
            row_text = "".join([td.text for td in tds])

            if "년" in row_text:
                for td in tds:
                    m = re.search(r"(\d{4})\s*년", td.text)
                    if m:
                        found_yr = int(m.group(1))
                        if year_1 is None:
                            year_1 = found_yr
                        elif year_2 is None and found_yr != year_1:
                            year_2 = found_yr

        # --- STEP 2: Extract Numeric Data per Category ---
        data_1 = {"year": year_1}
        data_2 = {"year": year_2}

        for row in rows:
            tds = row.find_elements(By.CSS_SELECTOR, "div[class*='td']")

            # Skip rows that don't have enough columns
            if len(tds) < 8:
                continue

            categories = tds[0].text.strip()
            # Filter non-category header rows
            if not categories or "구분" in categories or "년" in categories:
                continue

            # Extract numeric data from target columns
            # (Using index 5 and 7 as noted in your comments; adjust to 6/8 if needed)
            try:
                val_1_str = tds[6].text.replace(",", "").replace("\xa0", "").strip()
                val_2_str = tds[8].text.replace(",", "").replace("\xa0", "").strip()

                if val_1_str and val_2_str:
                    data_1[categories] = int(val_1_str)
                    data_2[categories] = int(val_2_str)
            except ValueError:
                continue

        # --- STEP 3: Construct DataFrame ---
        df_result = pd.DataFrame([data_1, data_2])
        cols = ["year"] + [c for c in df_result.columns if c != "year"]
        return df_result[cols]

    finally:
        driver.quit()


def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    target_configs = [
        ("20ecaec9b07f4978ab15f94b907ef94c", (2020, 2021)),
        ("beb02fb4c673425ba0c206e48cc34c5c", (2022, 2023)),
        ("c8913ff8727240b981e4841d2ad4ecc2", (2024, 2025)),
    ]

    print("🚀 [Pipeline] Selenium을 통한 동적 웹 크롤링 시작...")

    all_dfs = []

    for key, years in target_configs:
        target_url = (
            f"http://viewer.daejeon.go.kr:8080/SynapDocViewServer/viewer/doc.html"
            f"?key={key}&convType=html&convLocale=ko_KR&contextPath=/SynapDocViewServer/"
        )
        try:
            df = scrape_with_selenium(target_url, default_years=years)
            all_dfs.append(df)
            print(f"✅ Key [{key[:8]}...] (년도: {years[0]}, {years[1]}) 파싱 성공")
        except Exception:
            print(f"\n❌ Key [{key[:8]}...] 디버깅 상세 에러:")
            traceback.print_exc()

    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)

        if "year" in final_df.columns:
            final_df = final_df.sort_values(by="year").reset_index(drop=True)

        output_path = data_dir / "dmc_dj_const_2020_2025.csv"
        final_df.to_csv(output_path, index=False, encoding="utf-8-sig")

        print(f"\n🎉 [Success] 최종 데이터 저장 완료: {output_path}")
        print("\n[추출된 DataFrame 결과]")
        print(final_df)


if __name__ == "__main__":
    main()
