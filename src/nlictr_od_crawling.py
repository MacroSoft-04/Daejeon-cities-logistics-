import os
import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# 1. 디렉토리 설정
SAVE_DIR = "./data"
os.makedirs(SAVE_DIR, exist_ok=True)

# 2. 기초 데이터 정의
years_list = ["2019", "2020", "2021", "2022", "2023"]
regions = [
    "서울특별시",
    "부산광역시",
    "대구광역시",
    "인천광역시",
    "광주광역시",
    "대전광역시",
    "울산광역시",
    "경기도",
    "강원특별자치도",
    "충청북도",
    "충청남도",
    "전북특별자치도",
    "전라남도",
    "경상북도",
    "경상남도",
    "제주특별자치도",
    "세종특별자치시",
]
# 3. Edge Driver 실행
options = webdriver.EdgeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Edge(
    service=EdgeService(EdgeChromiumDriverManager().install()), options=options
)
wait = WebDriverWait(driver, 15)

url = "https://www.nlic.go.kr/nlic/frghtRoad0040.action"
all_years_df_list = []

try:
    driver.get(url)
    time.sleep(3)

    for year in years_list:
        print(f"\n==================================================")
        print(f"📅 [{year}년] 데이터 크롤링 진행 중...")

        for region in regions:
            print(f"  └ 📍 [{region}] 32번째 데이터 추출 중...", end="", flush=True)

            try:
                # 1. 연도 드롭다운 선택
                dropdown_year_elem = wait.until(
                    EC.presence_of_element_located((By.ID, "S_TOYEAR"))
                )
                dropdown_year = Select(dropdown_year_elem)
                dropdown_year.select_by_value(year)
                time.sleep(0.3)

                # 2. 출발지 드롭다운 선택
                dropdown_region = Select(driver.find_element(By.ID, "S_DEPART_AREA"))
                dropdown_region.select_by_visible_text(region)
                time.sleep(0.3)

                # 3. 기존 데이터 영역 요소를 미리 확보 (AJAX 스탈니스 감지용)
                old_elements = driver.find_elements(
                    By.CSS_SELECTOR, "div.Right_fixed ul.W_110px"
                )
                old_first_elem = old_elements[0] if old_elements else None

                # 4. 검색 버튼 클릭
                search_button = driver.find_element(
                    By.CSS_SELECTOR, "button.btn-md[type='submit']"
                )
                search_button.click()

                # AJAX 비동기 로딩 대기
                if old_first_elem:
                    try:
                        wait.until(EC.staleness_of(old_first_elem))
                    except:
                        pass

                time.sleep(2.5)  # AJAX 렌더링 보장 대기

                # 5. BeautifulSoup 파싱
                soup = BeautifulSoup(driver.page_source, "html.parser")
                data_uls = soup.select("div.Right_fixed ul.W_110px")

                # ⭐ [핵심] 32번째 ul.W_110px 태그 타겟팅 (인덱스 31)
                TARGET_INDEX = 208  # 32번째

                if len(data_uls) > TARGET_INDEX:
                    target_ul = data_uls[TARGET_INDEX]

                    # list_num_01 우선 탐색 (없으면 list_num_02 또는 ul 전체 텍스트)
                    target_li = target_ul.select_one(
                        "li.list_num_01"
                    ) or target_ul.select_one("li.list_num_02")
                    val_text = (
                        target_li.get_text(strip=True)
                        if target_li
                        else target_ul.get_text(strip=True)
                    )

                    # 콤마 제거 및 정수 변환
                    clean_num = re.sub(r"[^\d]", "", val_text.replace(",", ""))
                    val = int(clean_num) if clean_num else 0

                    # 1건 데이터 저장
                    temp_df = pd.DataFrame(
                        [{"연도": year, "출발지": region, "물동량_톤": val}]
                    )

                    all_years_df_list.append(temp_df)
                    print(f" -> 성공 (추출된 값: {val:,}톤)")
                else:
                    print(
                        f" -> ⚠️ 전체 ul 태그 수({len(data_uls)}개)가 32개 미만입니다."
                    )

            except Exception as reg_e:
                print(f" -> ❌ 에러 발생: {reg_e}")

    # 6. 최종 데이터 저장
    if all_years_df_list:
        final_df = pd.concat(all_years_df_list, ignore_index=True)
        save_path = os.path.join(
            SAVE_DIR, f"nlic_cargo_{years_list[0]}_{years_list[-1]}.csv"
        )
        final_df.to_csv(save_path, index=False, encoding="utf-8-sig")

        print(f"\n==================================================")
        print(f"🎉 성공적으로 크롤링 완료! 총 {len(final_df):,}건 데이터 수집됨.")
        print(f"📁 파일 저장 위치: {save_path}")
        print(f"==================================================")

except Exception as e:
    print(f"\n❌ 실행 중 에러: {e}")

finally:
    driver.quit()
