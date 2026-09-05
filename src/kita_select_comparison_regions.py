"""
====================================================================
* Author: Minseo Kim
* Purpose: Select comparison regions for the Daejeon trade analysis.
* Data Source:
    - data/processed/kita_regional_2025.csv
* Region selection criteria:
    - (i) adjacent to Daejeon within the Chungcheong area, or
    - (ii) a metropolitan city whose 2025 exports fall within 5x of Daejeon's.
* Output:
    - data/raw/kita_monthly_{region}_{YYYYMMDD}.xls
====================================================================
"""

from pathlib import Path
import pandas as pd

data_dir = Path("./data/processed")
file_path = data_dir / "kita_regional_2025.csv"
df = pd.read_csv(file_path)

codebook = pd.read_csv(data_dir / "codebook_관세청_시도코드_clean.csv")

REFERENCE_REGION = "대전"
SCALE_CEILING = 5.0
SCALE_FLOOR = 0.2

METROPOLITAN_CITIES = {"서울", "부산", "대구", "인천", "광주", "대전", "울산"}
CHUNGCHEONG = {"충남", "충북", "세종"}


def lookup(codebook, codebook_clean, sample):
    print("<codebook>\n", codebook.columns)
    print(codebook[codebook["비고"].notnull()])
    print("\n<sample>\n", sample.columns)
    print("\n<codebook_clean>\n", codebook_clean["시도명"].to_list())


def select_comparison_regions(summary: pd.DataFrame) -> pd.DataFrame:

    reference = df.loc[df["지역명"] == REFERENCE_REGION, "수출액"].iloc[0]
    df["배율"] = df["수출액"] / reference

    by_adjacency = df["지역명"].isin(CHUNGCHEONG)
    by_scale = df["지역명"].isin(METROPOLITAN_CITIES) & df["배율"].between(
        SCALE_FLOOR, SCALE_CEILING
    )

    df["포함사유"] = None
    df.loc[by_scale, "포함사유"] = "규모"
    df.loc[by_adjacency, "포함사유"] = "인접"
    df.loc[df["지역명"] == REFERENCE_REGION, "포함사유"] = "기준"
    df.rename(columns={"지역명": "시도명"}, inplace=True)

    return df[df["포함사유"].notna()].sort_values("배율", ascending=False)


result = select_comparison_regions(df)
result = result[["시도명", "수출액", "배율", "포함사유"]]

codebook_clean = codebook[~codebook["비고"].str.contains("이후", na=False)]
codebook_clean = codebook_clean[["시도코드", "시도명"]]
codebook_clean["시도명"] = codebook_clean["시도명"].replace(
    {
        "충청남도": "충남",
        "충청북도": "충북",
    }
)

pattern = "|".join(result["시도명"])

codebook_sido = codebook_clean[
    codebook_clean["시도명"].str.contains(
        pattern,
        na=False,
    )
].copy()

codebook_sido["시도명"] = codebook_sido["시도명"].str.extract(f"({pattern})")

lookup(codebook, codebook_clean, df)

df_merged = pd.merge(result, codebook_sido, on="시도명", how="outer")

df_merged.to_csv(
    data_dir / "comparison_regions.csv",
    index=False,
    encoding="utf-8-sig",
)
print("\n<df_merged>\n", df_merged)
print(f"Comparison regions saved to {data_dir / 'comparison_regions.csv'}")
