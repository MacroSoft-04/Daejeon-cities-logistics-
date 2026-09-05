"""
====================================================================
* Author: Minseo Kim
* Purpose: Select comparison regions for the Daejeon trade analysis.
* Data Source:
    - stat.kita.net/stat/kts/prod/ProdWholeList.screen
    - data/raw/지자체 수출입 총괄 _ 국내통계 - K-stat 수출입 무역통계_금액.csv
    - data/raw/지자체 수출입 총괄 _ 국내통계 - K-stat 수출입 무역통계_중량.csv
* Data Processing:
    - merge 금액 and 중량 files, reshape to long format
* Output:
    - data/processed/kita_regional_2025.csv
====================================================================
"""

from pathlib import Path
import pandas as pd

RAW_DIR = Path("./data/raw")
PROCESSED_DIR = Path("./data/processed")

FILES = {
    "금액": RAW_DIR / "지자체 수출입 총괄 _ 국내통계 - K-stat 수출입 무역통계_금액.csv",
    "중량": RAW_DIR / "지자체 수출입 총괄 _ 국내통계 - K-stat 수출입 무역통계_중량.csv",
}

HEADER_ROWS = [2, 3]


def process_kita_file(file_path):
    """Reshape a K-stat regional summary export into long format (region x year)."""

    df = pd.read_csv(file_path, header=HEADER_ROWS)

    df = df.drop(columns=["2024년", "순번"], level=0, errors="ignore")

    df.columns = df.columns.set_names(["연도", "지표"])
    df = df.set_index(("지역명", "지역명"))
    df.index.name = "지역명"
    df_stacked = df.stack(level="연도", future_stack=True).reset_index()

    df_stacked["연도"] = df_stacked["연도"].str.extract(r"(\d{4})").astype("int64")

    return df_stacked


amount, weight = (process_kita_file(p) for p in FILES.values())

merged = amount.merge(
    weight, on=["지역명", "연도"], how="outer", suffixes=("_금액", "_중량")
)

merged = merged.rename(columns={"수지": "수지_금액", "차이": "수지_중량"})
merged = merged[merged["지역명"] != "총계"].copy()

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
merged.to_csv(
    PROCESSED_DIR / "kita_regional_2025.csv", index=False, encoding="utf-8-sig"
)
print(f"Saved {len(merged)} rows for {merged['지역명'].nunique()} regions")
