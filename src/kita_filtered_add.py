import pandas as pd
from pathlib import Path
from kita_merged_clean import check_calculations, RATIO_COLUMNS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

MONTHLY_INPUT = PROCESSED_DIR / "kita_regional_monthly_filtered.csv"
YEARLY_INPUT = PROCESSED_DIR / "kita_regional_yearly_filtered.csv"

MONTHLY_PATH = PROCESSED_DIR / "kita_regional_monthly_added.csv"
YEARLY_PATH = PROCESSED_DIR / "kita_regional_yearly_added.csv"

SOURCES = {"monthly": MONTHLY_INPUT, "yearly": YEARLY_INPUT}
OUTPUTS = {"monthly": MONTHLY_PATH, "yearly": YEARLY_PATH}

SCALE_GROUP = ["광주", "대구", "부산"]
ADJACENT_GROUP = ["충남", "충북", "세종"]
ADJACENT_CONSISTENT = ["충남(세종 포함)", "충북"]
COMBINED = "충남(세종 포함)"

SUM_COLUMNS = [
    "수출액_백만불",
    "수입액_백만불",
    "수지액_백만불",
    "수출중량_천톤",
    "수입중량_천톤",
]

COMBINED = "충남(세종 포함)"


def add_chungnam_with_sejong(df, keys):
    """세종 took 연기군 from 충남 in July 2012; adding it back keeps 충남's boundary
    roughly constant across 2012 (세종 also took small parts of 공주 and 충북 청원).
    Published columns are summed; derived ones are recomputed from the sums."""
    parts = df[df["지역명"].isin(["충남", "세종"])]
    combined = parts.groupby(keys, as_index=False)[SUM_COLUMNS].sum(min_count=1)
    combined["수지중량_천톤"] = combined["수출중량_천톤"] - combined["수입중량_천톤"]
    # 백만불 / 천톤 = USD per kg, same as in the cleaner
    combined["수출단가_USD_kg"] = combined["수출액_백만불"] / combined["수출중량_천톤"]
    combined["수입단가_USD_kg"] = combined["수입액_백만불"] / combined["수입중량_천톤"]
    combined["중량비_수입대수출"] = (
        combined["수입중량_천톤"] / combined["수출중량_천톤"]
    )
    combined["지역명"] = COMBINED
    return pd.concat([df, combined], ignore_index=True)


def check_combined(df, index, cols=SUM_COLUMNS):
    """Rebuild the combined rows from 충남 and 세종 separately, so the check doesn't
    reuse the groupby it's checking; before 세종's launch it must equal 충남 alone."""
    by_region = {
        r: df[df["지역명"] == r].set_index(index)[cols]
        for r in ["충남", "세종", COMBINED]
    }
    expected = by_region["충남"].add(by_region["세종"], fill_value=0)
    gap = (by_region[COMBINED] - expected).abs().max()
    print(f"{COMBINED} vs 충남 + 세종, max abs gap:\n{gap.to_string()}")
    if (gap > 1e-6).any():
        raise ValueError(f"{COMBINED} doesn't equal 충남 + 세종")

    sample = pd.concat(
        {r: f["수출액_백만불"] for r, f in by_region.items()}, axis=1, sort=True
    )
    start = by_region["세종"]["수출액_백만불"].dropna().index.min()
    pos = sample.index.get_loc(start)
    print(f"\n{sample.iloc[max(pos - 2, 0) : pos + 2].to_string()}")


def check_sorted(df, time_col):
    """Lag features use shift(), which means 'previous row'; that's only the
    previous period if each region's rows run oldest to newest."""
    ok = df.groupby("지역명")[time_col].apply(lambda s: s.is_monotonic_increasing)
    if not ok.all():
        raise ValueError(f"not sorted by {time_col} within: {sorted(ok[~ok].index)}")
    print(f"\nsorted by {time_col} within all {len(ok)} regions")


def check_ratio_bounds(df, index):
    """A pooled ratio (a1+a2)/(w1+w2) always lies between the two regions' own
    ratios; outside that range means the ratios were summed or built from the wrong columns.
    """
    for col in RATIO_COLUMNS:
        ratio = pd.concat(
            {
                r: df[df["지역명"] == r].set_index(index)[col]
                for r in ["충남", "세종", COMBINED]
            },
            axis=1,
        ).dropna()
        lo = ratio[["충남", "세종"]].min(axis=1)
        hi = ratio[["충남", "세종"]].max(axis=1)
        outside = ratio[
            (ratio[COMBINED] < lo * (1 - 1e-9)) | (ratio[COMBINED] > hi * (1 + 1e-9))
        ]
        if not outside.empty:
            raise ValueError(
                f"{col}: {COMBINED} outside 충남–세종 range\n{outside.head().to_string()}"
            )
        print(f"{col}: {COMBINED} within 충남–세종 range ({len(ratio)} rows)")


if __name__ == "__main__":
    monthly = pd.read_csv(MONTHLY_INPUT, encoding="utf-8-sig", parse_dates=["연월"])
    yearly = pd.read_csv(YEARLY_INPUT, encoding="utf-8-sig")

    monthly = add_chungnam_with_sejong(monthly, keys=["연도", "연월"]).sort_values(
        ["지역명", "연월"], ignore_index=True
    )
    yearly = add_chungnam_with_sejong(yearly, keys=["연도"]).sort_values(
        ["지역명", "연도"], ignore_index=True
    )

    for label, df, index in [("monthly", monthly, "연월"), ("yearly", yearly, "연도")]:
        rows = df[df["지역명"] == COMBINED]
        if rows.empty:
            raise ValueError(f"{label}: no {COMBINED} rows were added")
        print(f"\n---{label}---")
        check_combined(df, index)
        check_sorted(df, index)
        print("\n<calculations>")
        check_calculations(rows, label=f"{label} {COMBINED}")
        print("\n<ratio bounds>")
        check_ratio_bounds(df, index)
        rates = [c for c in df.columns if c.endswith("증감률")]
        assert rows[rates].isna().all(axis=None), f"{label}: 증감률 should be empty"

    monthly.to_csv(MONTHLY_PATH, index=False, encoding="utf-8-sig")
    yearly.to_csv(YEARLY_PATH, index=False, encoding="utf-8-sig")
