"""
====================================================================
* Author: Minseo Kim
* Data Sources:
    - 수출입 무역통계/지역별 실적_대전광역시(2020~2025)
    - tradedata/regional performance_Deajeon
    - https://tradedata.go.kr/cts/index.do
* import:
    - tradedata_ragional_20.csv
    - tradedata_ragional_21.csv
    - tradedata_ragional_22.csv
    - tradedata_ragional_23.csv
    - tradedata_ragional_24.csv
    - tradedata_ragional_25.csv
    - tradedata_ragional_26.csv
* Data Cleaning:
* Output: data/kosis_clean_ipi_long.csv
====================================================================
"""

from pathlib import Path
import numpy as np  # 안 써도 상관없지만 유지
import pandas as pd

base_dir = Path(".")
data_dir = base_dir / "data"
data_dir.mkdir(parents=True, exist_ok=True)
save_dir = base_dir / "data"

nums = [20, 21, 22, 23, 24, 25, 26]
dfs = []

for num in nums:
    file_path = data_dir / f"tradedata_dj_{num}.csv"

    # 1. 파일 존재 여부 확인 후 로드
    if file_path.exists():
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            # 품목명 한자/특수문자 대응을 위해 cp949 권장
            df = pd.read_csv(file_path, encoding="cp949")

        # 2. '기간' 컬럼이 '총계'인 행 제거
        clean_df = df[df["기간"] != "총계"].copy()
        dfs.append(clean_df)

# 3. 데이터가 있을 때만 결합 및 저장
if dfs:
    final_df = pd.concat(dfs, ignore_index=True)
    save_path = save_dir / "tradedata_dj_2020_2026.csv"
    final_df.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(f"✅ 파일 저장 완료: {save_path.resolve()}")
else:
    print("⚠️ 불러올 수 있는 CSV 파일이 없습니다. 파일 경로 및 파일명을 확인해 주세요.")
