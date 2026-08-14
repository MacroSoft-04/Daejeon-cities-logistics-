"""
====================================================================
* Author: Minseo Kim
* Data Source:
    - KOSIS 전국사업체조사 (statsConfmNo 101037), 대전, 2020~2024
    - Industry major groups; 사업체수 / 종사자수 / 매출액
* Survey caveats:
    - Register-based population from the 2021 survey onward; the published
      table is back-filled to 2020, so 2020~2024 share one basis. Do not
      join to pre-2020 (survey-based) figures.
    - Fieldwork ran Jun-Jul over 35 days for the 2020 reference year and
      Feb-Mar over 25 days thereafter. 2021 is used as the index base year
      because its conditions match the later years.
    - Establishment-level (사업체), not enterprise-level (기업체): one firm
      with several sites counts more than once.
* Output: data/processed/estab_survey_daejeon_long.csv
====================================================================
"""

from pathlib import Path

from kosis_utils import read_kosis_long

base_dir = Path("./data")
SRC = base_dir / "raw/시도·산업별_사업체수__종사자수_및_매출액_’20___20260815082431.csv"
OUT = base_dir / "processed/kosis_estab_survey.csv"

BASE_YEAR = 2021

OUT.parent.mkdir(parents=True, exist_ok=True)

df = read_kosis_long(SRC, id_cols=["행정구역별", "산업별"])
df = df[df["산업별"] != "산업별"]

# Index each series to the base year so metrics with different units can share
# an axis; kept as a column rather than a separate file to avoid drift.
base = (
    df[df["연도"] == BASE_YEAR]
    .set_index(["행정구역별", "산업별", "지표"])["값"]
    .rename("기준값")
)
df = df.join(base, on=["행정구역별", "산업별", "지표"])
df["지수"] = (df["값"] / df["기준값"] * 100).round(2)
df = df.drop(columns="기준값")

if "비고" in df.columns:
    df = df.drop(columns=["비고"])

df["산업코드"] = df["산업코드"].fillna(0)

df.to_csv(OUT, index=False, encoding="utf-8-sig")

print(f"{len(df):,} rows -> {OUT}")
print(f"industries: {df['산업별'].nunique()} | years: {sorted(df['연도'].unique())}")
print(f"missing: {df['값'].isna().sum()}")
