import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import Select
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# 1. Edge Driver 실행
driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))

url = "https://www.nlic.go.kr/nlic/frghtRoad0020.action"
driver.get(url)
time.sleep(3)

test_year = "2019"
print(f"=== [{test_year}년 데이터 단일상품 검증 시작] ===")

try:
    # 연도 선택 및 조회
    dropdown = Select(driver.find_element(By.ID, "S_TOYEAR"))
    dropdown.select_by_value(test_year)
    time.sleep(1)

    search_button = driver.find_element(By.CSS_SELECTOR, "button.btn-md[type='submit']")
    search_button.click()
    print("데이터 조회 요청 중... 5초 대기")
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # ----------------------------------------------------
    # 1. 품목 리스트 (행 헤더)
    # ----------------------------------------------------
    item_elements = soup.select("div.Left_fixed li.con_list_1")

    items_list = [
        li.get_text(strip=True)
        for li in item_elements
        if li.get_text(strip=True)  # 빈 문자열 제외
    ]

    # ----------------------------------------------------
    # 2. (지역, 구분) 컬럼 (열 헤더)
    # ----------------------------------------------------
    # div.Right_fixed 바로 아래의 헤더 ul.W_320px 추출 (con1 경로 제거)
    header_uls = soup.select("div.Right_fixed ul.W_320px")

    # 본문 데이터 ul과 구분하기 위해, 헤더에 해당하는 상단 17개만 정확히 잘라냅니다.
    # (NLIC 도로화물 사이트의 헤더 영역은 상단 17개 ul로 구성됨)
    # 만약 동적으로 헤더 개수를 파악하려면 list_sb_1(지역명)이 들어있는 ul만 필터링합니다.
    header_uls = [ul for ul in header_uls if ul.select_one("li.list_sb_1")]

    if not header_uls:
        raise ValueError(
            "웹페이지에서 헤더(지역) 정보를 찾을 수 없습니다. (header_uls가 비어있음)"
        )

    columns_list = []

    for ul in header_uls:
        # 1) 대분류 (지역명: 서울, 부산, 대구 ...)
        region_el = ul.select_one("li.list_sb_1")
        region_name = region_el.get_text(strip=True) if region_el else ""

        # 2) 소분류 (구분값: 반입, 반출, 합계 등)
        sub_spans = ul.select("li.list_sb_2 span")
        sub_types = [
            span.get_text(strip=True) for span in sub_spans if span.get_text(strip=True)
        ]

        # 3) (지역, 구분) 튜플 바인딩
        for sub in sub_types:
            columns_list.append((region_name, sub))

    # ----------------------------------------------------
    # 3. 본문 수치 데이터 파싱
    # ----------------------------------------------------
    all_uls = soup.select("div.Right_fixed ul.W_320px")
    num_header_uls = len(header_uls)  # 17개
    data_uls = all_uls[num_header_uls:]

    matrix_data = []
    num_regions = num_header_uls  # 17개 시/도

    # num_regions가 0일 경우 발생하는 range() 에러 원천 차단
    if num_regions == 0:
        raise ValueError("지역 개수(num_regions)가 0입니다. HTML 셀렉터를 확인하세요.")

    # 전체 data_uls를 17개씩 싹둑 잘라서 (1개 품목 단위로) 순회
    for row_idx in range(0, len(data_uls), num_regions):
        item_uls = data_uls[row_idx : row_idx + num_regions]
        row_values = []

        for ul in item_uls:
            spans = ul.select("li.list_sb_3 span")
            for span in spans:
                val_text = span.get_text(strip=True).replace(",", "")
                # 숫자만 추출 (비어있거나 이상한 문자일 경우 0 처리)
                clean_num = re.sub(r"[^\d]", "", val_text)
                val = int(clean_num) if clean_num else 0
                row_values.append(val)

        # 컬럼 수와 매칭되는 행 데이터만 수집
        if len(row_values) == len(columns_list):
            matrix_data.append(row_values)
    # ----------------------------------------------------
    # 4. 판다스 DataFrame 구성 (MultiIndex 전체 unstack/stack 명시)
    # ----------------------------------------------------
    # 1) 품목 수와 수치 행 데이터 개수 검증
    if len(items_list) != len(matrix_data):
        print(
            f"⚠️ 경고: 품목 수({len(items_list)})와 수치 행 수({len(matrix_data)})가 일치하지 않습니다!"
        )

    # 2) MultiIndex 생성 시 레벨 이름 명시
    multi_cols = pd.MultiIndex.from_tuples(columns_list, names=["지역", "구분"])

    # 3) 2차원 데이터프레임 매칭 및 Index 이름 지정
    df_matrix = pd.DataFrame(data=matrix_data, index=items_list, columns=multi_cols)
    df_matrix.index.name = "품목"

    # 4) Long-format 변환
    # level=["지역", "구분"]으로 두 컬럼 레벨을 한 번에 stack 처리합니다.
    df_stacked = df_matrix.stack(level=["지역", "구분"], future_stack=True)

    # Series를 DataFrame으로 변환하며 값 컬럼명을 "물동량_톤"으로 지정
    df_long = df_stacked.reset_index(name="물동량_톤")
    df_long["연도"] = test_year
    # ----------------------------------------------------
    # 🧪 [정밀 검증 1] 수치 정합성 체크 (반입 + 반출 == 합계?)
    # ----------------------------------------------------
    print("\n" + "=" * 60)
    print("🔍 [정밀 검증 1] '반입 + 반출 = 합계' 수치 공식 검증")

    df_check = df_long.pivot_table(
        index=["품목", "지역"],
        columns="구분",
        values="물동량_톤",
        aggfunc="first",
    ).reset_index()

    present_cols = set(df_check.columns)
    if {"반입", "반출", "합계"}.issubset(present_cols):
        df_check["calc_sum"] = df_check["반입"] + df_check["반출"]
        df_check["is_correct"] = df_check["calc_sum"] == df_check["합계"]

        mismatch = df_check[~df_check["is_correct"]]

        if mismatch.empty:
            print("✅ [PASS] 모든 행의 (반입 + 반출 = 합계) 수치가 100% 일치합니다!")
        else:
            print(f"⚠️ [FAIL] 불일치 데이터가 {len(mismatch)}건 발견되었습니다!")
            print(mismatch.head())
    else:
        print(f"⚠️ 구분 컬럼 인식 실패 (현재 인식된 구분 목록: {list(present_cols)})")

    # ----------------------------------------------------
    # 🧪 [정밀 검증 2] 샘플 데이터 출력
    # ----------------------------------------------------
    print("\n🔍 [정밀 검증 2] 샘플 데이터 3건 매칭 출력")
    positive_df = df_long[df_long["물동량_톤"] > 0]
    sample_size = min(3, len(positive_df))

    if sample_size > 0:
        sample_df = positive_df.sample(sample_size, random_state=42)
        for idx, row in sample_df.iterrows():
            print(
                f"  📌 [{row['품목']}] | 지역: {row['지역']} | 구분: {row['구분']} --> 📦 {row['물동량_톤']:,} 톤"
            )
    else:
        print("  ⚠️ 0보다 큰 물동량 데이터가 없습니다.")

    # ----------------------------------------------------
    # 🧪 [정밀 검증 3] 결측치 및 음수 점검
    # ----------------------------------------------------
    print("\n🔍 [정밀 검증 3] 결측치 및 데이터 무결성 점검")
    null_count = df_long["물동량_톤"].isnull().sum()
    negative_count = (df_long["물동량_톤"] < 0).sum()

    print(f"- NaN(결측치) 개수: {null_count}개 (정상: 0개)")
    print(f"- 음수 수치 개수: {negative_count}개 (정상: 0개)")

    # ----------------------------------------------------
    # 🧪 [정밀 검증 4] 품목별 전국 총 합계 Top 3
    # ----------------------------------------------------
    print("\n🔍 [정밀 검증 4] 물동량 Top 3 품목")
    df_sum_by_item = (
        df_long[df_long["구분"] == "합계"]
        .groupby("품목")["물동량_톤"]
        .sum()
        .sort_values(ascending=False)
    )

    if not df_sum_by_item.empty:
        print(df_sum_by_item.head(3).to_string())
    else:
        print("⚠️ '합계' 구분을 찾을 수 없어 전체 총합 Top 3로 대체합니다:")
        print(
            df_long.groupby("품목")["물동량_톤"]
            .sum()
            .sort_values(ascending=False)
            .head(3)
            .to_string()
        )

    print("=" * 60)

except Exception as e:
    print(f"❌ 검증 중 에러 발생: {e}")

finally:
    driver.quit()
