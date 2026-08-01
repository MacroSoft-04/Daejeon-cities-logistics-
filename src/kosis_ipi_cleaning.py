"""
====================================================================
* Author: Minseo Kim
* Data Sources:
    - KOSIS 시도/산업별 광공업 생산지수(2018~2026)
    - https://www.kosis.or.kr/kosis/kosis/main.do?page=main&menuNo=1000
* Data Cleaning:
    - Remove unnecessary/unnamed columns
    - Convert data type to float
    - Replace NaN with None
    - Convert date format to 'YYYY-MM-DD'
* Data Processing:
    - Unpivot (Melt) the data to long format
* Output: data/kosis_clean_ipi_long.csv
====================================================================
"""

from pathlib import Path
import numpy as np
import pandas as pd

base_dir = Path(".")
data_dir = base_dir / "data"
data_dir.mkdir(parents=True, exist_ok=True)
save_dir = base_dir / "data"

# 1. 데이터 불러오기 (인코딩 예외 처리)
file_path = data_dir / "kosis_raw_ipi.csv"

try:
    df = pd.read_csv(file_path, encoding="cp949")
except UnicodeDecodeError:
    try:
        df = pd.read_csv(file_path, encoding="euc-kr")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="utf-8-sig")

# 2. 컬럼명 양쪽 공백 제거 및 Unnamed(빈 끝 열) 자동 제거
df.columns = df.columns.str.strip()
df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

# 3. 불필요한 컬럼('단위') 제거
if "단위" in df.columns:
    df = df.drop(columns=["단위"])

# 4. 날짜/월별 컬럼 식별
id_vars = ["시도별", "산업별", "항목"]
date_cols = [col for col in df.columns if col not in id_vars]

# 5. 결측치 및 빈 문자열 처리
df[date_cols] = df[date_cols].apply(lambda x: x.astype(str).str.strip())
df[date_cols] = df[date_cols].replace(
    {"": np.nan, "-": np.nan, "nan": np.nan, None: np.nan}
)

# 6. 수치형 데이터(float)로 변환
for col in date_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# -------------------------------------------------------------
# [추가 전처리] 시계열 분석/그래프 작성을 위한 Unpivot (Melt) 과정
# -------------------------------------------------------------
df_long = df.melt(
    id_vars=id_vars, value_vars=date_cols, var_name="연월", value_name="지수"
)

# '2018.01 월' 형태의 문자열을 정식 날짜 타입('2018-01-01')으로 변환
df_long["연월_clean"] = (
    df_long["연월"].str.replace(" 월", "").str.replace(".", "-", regex=False)
)

# errors="coerce"를 추가하여 안전하게 날짜 변환
df_long["날짜"] = pd.to_datetime(df_long["연월_clean"] + "-01", errors="coerce")
df_long = df_long.drop(columns=["연월_clean"])

# 날짜 변환 실패한 행(결측 열 등) 제거
df_long = df_long.dropna(subset=["날짜"])

# 컬럼 순서 재정렬 및 정렬
df_long = df_long[["시도별", "산업별", "항목", "날짜", "지수"]].sort_values(
    by=["시도별", "산업별", "항목", "날짜"]
)

df_long.to_csv(
    save_dir / "kosis_clean_ipi_long.csv", index=False, encoding="utf-8-sig"
)  # 시계열 분석용 세로 형태

print("전처리가 성공적으로 완료되었습니다!")
print(f"1. Wide 형태 데이터 크기: {df.shape}")
print(f"2. Long(시계열) 형태 데이터 크기: {df_long.shape}")
