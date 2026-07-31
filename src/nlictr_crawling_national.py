import os
import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import Select
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# 저장할 데이터 디렉토리 생성
SAVE_DIR = "NLIC_tr_pf/data"
os.makedirs(SAVE_DIR, exist_ok=True)

# 1. Edge Driver 실행
driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))

url = "https://www.nlic.go.kr/nlic/frghtRoad0020.action"
driver.get(url)
time.sleep(3)

# 수집 대상 연도 리스트 정의
years_list = ["2019", "2020", "2021", "2022", "2023"]
print(
    f"🚀 [총 {len(years_list)}개 연도({years_list[0]}~{years_list[-1]}) 도로화물 물동량 데이터 크롤링 시작]"
)

all_years_df_list = []  # 연도별 데이터프레임을 모을 리스트

try:
    for year in years_list:
        print(f"\n--------------------------------------------------")
        print(f"📅 [{year}년] 데이터 크롤링 진행 중...")

        # 2. 연도 선택 및 조회
        dropdown = Select(driver.find_element(By.ID, "S_TOYEAR"))
        dropdown.select_by_value(year)
        time.sleep(1)

        search_button = driver.find_element(
            By.CSS_SELECTOR, "button.btn-md[type='submit']"
        )
        search_button.click()
        print(f"⏳ 데이터 조회 요청 중... (5초 대기)")
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # ----------------------------------------------------
        # 1) 품목 리스트 (행 헤더) 추출
        # ----------------------------------------------------
        item_elements = soup.select("div.Left_fixed li.con_list_1")
        items_list = [
            li.get_text(strip=True) for li in item_elements if li.get_text(strip=True)
        ]

        # ----------------------------------------------------
        # 2) (지역, 구분) 열 헤더 추출
        # ----------------------------------------------------
        header_uls = soup.select("div.Right_fixed ul.W_320px")
        header_uls = [ul for ul in header_uls if ul.select_one("li.list_sb_1")]

        if not header_uls:
            print(f"⚠️ [{year}년] 헤더(지역) 정보를 찾지 못해 건너뜁니다.")
            continue

        columns_list = []
        for ul in header_uls:
            region_el = ul.select_one("li.list_sb_1")
            region_name = region_el.get_text(strip=True) if region_el else ""

            sub_spans = ul.select("li.list_sb_2 span")
            sub_types = [
                span.get_text(strip=True)
                for span in sub_spans
                if span.get_text(strip=True)
            ]

            for sub in sub_types:
                columns_list.append((region_name, sub))

        # ----------------------------------------------------
        # 3) 본문 수치 데이터 파싱
        # ----------------------------------------------------
        all_uls = soup.select("div.Right_fixed ul.W_320px")
        num_header_uls = len(header_uls)
        data_uls = all_uls[num_header_uls:]

        matrix_data = []
        num_regions = num_header_uls

        if num_regions == 0:
            print(f"⚠️ [{year}년] 지역 개수가 0이라 건너뜁니다.")
            continue

        for row_idx in range(0, len(data_uls), num_regions):
            item_uls = data_uls[row_idx : row_idx + num_regions]
            row_values = []

            for ul in item_uls:
                spans = ul.select("li.list_sb_3 span")
                for span in spans:
                    val_text = span.get_text(strip=True).replace(",", "")
                    clean_num = re.sub(r"[^\d]", "", val_text)
                    val = int(clean_num) if clean_num else 0
                    row_values.append(val)

            if len(row_values) == len(columns_list):
                matrix_data.append(row_values)

        # ----------------------------------------------------
        # 4) DataFrame 생성 & Long-format 변환
        # ----------------------------------------------------
        multi_cols = pd.MultiIndex.from_tuples(columns_list, names=["지역", "구분"])
        df_matrix = pd.DataFrame(data=matrix_data, index=items_list, columns=multi_cols)
        df_matrix.index.name = "품목"

        df_stacked = df_matrix.stack(level=["지역", "구분"], future_stack=True)
        df_long = df_stacked.reset_index(name="물동량_톤")
        df_long["연도"] = year

        # 컬럼 순서 정돈 (연도, 품목, 지역, 구분, 물동량_톤)
        df_long = df_long[["연도", "품목", "지역", "구분", "물동량_톤"]]

        all_years_df_list.append(df_long)
        print(f"✨ [{year}년] 수집 완료 ({len(df_long):,}행)")

    # ----------------------------------------------------
    # 5. 전체 연도 데이터 병합 및 저장
    # ----------------------------------------------------
    if all_years_df_list:
        final_df = pd.concat(all_years_df_list, ignore_index=True)

        save_filename = f"nlic_cargo_{years_list[0]}_{years_list[-1]}.csv"
        save_path = os.path.join(SAVE_DIR, save_filename)
        final_df.to_csv(save_path, index=False, encoding="utf-8-sig")

        print(f"\n================================------------------")
        print(f"🎉 모든 연도 크롤링 및 통합 저장 완료!")
        print(f"📊 총 수집 데이터: {len(final_df):,}건")
        print(f"📁 파일 저장 경로: {save_path}")
        print(f"================================------------------")
    else:
        print("⚠️ 수집된 데이터가 전혀 없습니다.")

except Exception as e:
    print(f"❌ 크롤링 중 에러 발생: {e}")

finally:
    driver.quit()
