"""Select comparison regions for the Daejeon trade analysis.

Criterion is fixed before looking at any analysis output: a region qualifies if
it is (i) adjacent to Daejeon within the Chungcheong area, or (ii) a metropolitan
city whose 2025 exports fall within 5x of Daejeon's.
"""

from pathlib import Path
import pandas as pd

data_dir = Path("./data/processed")
file_path = data_dir / "kita_regional_summary.csv"
df = pd.read_csv(file_path)

REFERENCE_REGION = "대전"
SCALE_CEILING = 5.0
SCALE_FLOOR = 0.2

METROPOLITAN_CITIES = {"서울", "부산", "대구", "인천", "광주", "대전", "울산"}
CHUNGCHEONG = {"충남", "충북", "세종"}


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

    return df[df["포함사유"].notna()].sort_values("배율", ascending=False)


result = select_comparison_regions(df)
print(result[["지역명", "수출액", "배율", "포함사유"]])
