"""
====================================================================
* Author: Minseo Kim
* Purpose:
    - Add a 충남(세종 포함) series to the 관세청 HS-chapter panel so the
      adjacent-region comparison can use the same boundary as KITA's
      충남(세종 포함) for years before 2013.
* Input:
    - data/processed/tradedata_2000_2025_sectioned.csv
      (지역명 comes from tradedata_merged_clean.py via tradedata_section.sql)
* Output:
    - data/processed/tradedata_2000_2025_added.csv
* Notes:
    - 관세청 already reports every year on today's boundary (세종 from 2000),
      so the original 충남 and 세종 rows are kept; the combined rows are added.
    - Counts, amounts and 무역수지 are summed; 비중 is recomputed from the sums.
====================================================================
"""

import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

INPUT = PROCESSED_DIR / "tradedata_2000_2025_sectioned.csv"
SAVE_PATH = PROCESSED_DIR / "tradedata_2000_2025_added.csv"

YEAR = "기간"
HS_KEYS = [YEAR, "부코드", "부명약칭", "부명_공식", "류코드", "류명약칭", "류명_공식"]
SUM_COLUMNS = [
    "수출건수",
    "수출금액",
    "수입건수",
    "수입금액",
    "무역수지",
]
SORT_KEYS = ["지역", YEAR, "류코드"]

COMBINED_PARTS = ["충청남도", "세종특별자치시"]
COMBINED = "충청남도(세종특별자치시 포함)"


def add_chungnam_with_sejong(df, sum_cols=SUM_COLUMNS, index=HS_KEYS):
    """세종 took 연기군 from 충남 in July 2012; adding it back keeps 충남's boundary
    roughly constant across 2012 (세종 also took small parts of 공주 and 충북 청원).
    Published columns are summed; derived ones are recomputed from the sums."""
    parts = df[df["지역"].isin(COMBINED_PARTS)].copy()
    combined = parts.groupby(index, as_index=False)[sum_cols].sum()
    combined["지역"] = COMBINED
    combined["수출비중"] = (
        combined["수출금액"]
        * 100
        / combined["수출금액"]
        .groupby(combined[YEAR])
        .transform("sum")
        .replace(0, float("nan"))
    ).round(2)
    combined["수입비중"] = (
        combined["수입금액"]
        * 100
        / combined["수입금액"]
        .groupby(combined[YEAR])
        .transform("sum")
        .replace(0, float("nan"))
    ).round(2)
    return pd.concat([df, combined], ignore_index=True)


def check_combined(df, cols=SUM_COLUMNS, index=HS_KEYS):
    """Rebuild the combined rows from 충청남도 and 세종 separately, so the check doesn't
    reuse the groupby it's checking; before 세종's launch it must equal 충남 alone."""
    region = ["충청남도", "세종특별자치시", COMBINED]
    by_region = {
        r: (
            df[df["지역"] == r]
            .groupby(index, as_index=False)[cols]
            .sum()
            .set_index(index)
        )
        for r in region
    }
    expected = by_region["충청남도"].add(by_region["세종특별자치시"], fill_value=0)

    actual, expected = by_region[COMBINED].align(
        expected, join="outer", axis=0, fill_value=0
    )

    gap = (actual - expected).abs().max()
    print(f"{COMBINED} vs 충청남도 + 세종특별자치시, max abs gap:\n{gap}")
    if (gap > 1e-6).any():
        raise ValueError(f"{COMBINED} doesn't equal 충청남도 + 세종특별자치시")

    sample = pd.concat({r: f[cols] for r, f in by_region.items()}, axis=1, sort=True)
    start = by_region["세종특별자치시"][SUM_COLUMNS].dropna().index.min()
    pos = sample.index.get_loc(start)
    print(f"\n{sample.iloc[max(pos - 2, 0) : pos + 2].T.to_string()}")


def check_sorted(df):
    """Lag features use shift(), which means 'previous row'; that's only the
    previous period if each region's rows run oldest to newest."""
    ok = df.groupby("지역")[YEAR].apply(lambda s: s.is_monotonic_increasing)
    if not ok.all():
        raise ValueError(f"not sorted by {YEAR} within: {sorted(ok[~ok].index)}")
    print(f"\nsorted by {YEAR} within all {len(ok)} regions")


RATIO_COLUMNS = ["수출비중", "수입비중"]


def check_ratio_bounds(df, index):
    """A pooled ratio (a1+a2)/(w1+w2) always lies between the two regions' own
    ratios; outside that range means the ratios were summed or built from the wrong columns.
    """
    for col in RATIO_COLUMNS:
        ratio = pd.concat(
            {
                r: df[df["지역"] == r].set_index(index)[col]
                for r in ["충청남도", "세종특별자치시", COMBINED]
            },
            axis=1,
        ).dropna()
        lo = ratio[["충청남도", "세종특별자치시"]].min(axis=1)
        hi = ratio[["충청남도", "세종특별자치시"]].max(axis=1)
        outside = ratio[
            (ratio[COMBINED] < lo * (1 - 1e-9)) | (ratio[COMBINED] > hi * (1 + 1e-9))
        ]
        if not outside.empty:
            raise ValueError(
                f"{col}: {COMBINED} outside 충청남도–세종 range\n{outside.head().to_string()}"
            )
        print(f"{col}: {COMBINED} within 충청남도–세종 range ({len(ratio)} rows)")


if __name__ == "__main__":
    df = pd.read_csv(INPUT, encoding="utf-8-sig")
    added = add_chungnam_with_sejong(df).reset_index(drop=True)

    rows = added[added["지역"] == COMBINED]
    if rows.empty:
        raise ValueError(f"no {COMBINED} rows were added")
    print("\n<check_combined>")
    check_combined(added, index=HS_KEYS)
    print("\n<check_sorted>")
    check_sorted(added)
    print("\n<ratio bounds>")
    check_ratio_bounds(added, index=HS_KEYS)
    rates = [c for c in added.columns if c.endswith("증감률")]
    assert rows[rates].isna().all(axis=None), f"증감률 should be empty"

    added.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")
