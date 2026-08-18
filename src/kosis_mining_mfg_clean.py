"""
====================================================================
* Author: Minseo Kim
* Data Source:
    - KOSIS 광업제조업조사, 시도별 주요지표, 2020~2024
    - 사업체수 / 종사자수 / 급여액 / 출하액 / 주요생산비 / 부가가치 / 유형자산
* Survey caveats:
    - Covers establishments with 10 or more employees only. The universe
      differs from 전국사업체조사, so counts from the two must never be
      plotted on a shared axis; compare them as separate series instead.
    - "X" marks values withheld for confidentiality and "-" marks not
      applicable. Both are NaN here, distinguished by the 비고 column.
* Output: data/processed/mining_mfg_by_sido_long.csv
====================================================================
"""

from pathlib import Path

from kosis_utils import read_kosis_long

base_dir = Path("./data")
SRC = base_dir / "raw/시도_시군구__산업분류별_주요지표_10명_이상__20260814140423.csv"
OUT = base_dir / "processed/kosis_mining_mfg.csv"

OUT.parent.mkdir(parents=True, exist_ok=True)

df = read_kosis_long(SRC, id_cols=["시도별", "산업별"])
df = df[df["산업별"] != "산업별"]


df.loc[df["비고"] == "-", "값"] = 0

df.to_csv(OUT, index=False, encoding="utf-8-sig")

print(f"{len(df):,} rows -> {OUT}")
print(f"metrics: {df['지표'].unique().tolist()}")
print(
    f"missing: {df['값'].isna().sum()} | markers: {df['비고'].value_counts().to_dict()}"
)
