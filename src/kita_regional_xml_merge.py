"""
====================================================================
* Author: Minseo Kim
* Purpose:
    - Parse KITA regional monthly downloads into one long panel and split
      it into monthly and yearly rows, keeping the source's columns, units
      and published values.
    - Validate each download's structure, and cross-check the yearly figures
      against the K-stat summary table.
* Input:
    - data/raw/kita/kita_monthly_<region>_<YYYYMMDD>.xls
    - data/processed/kita_regional_2025.csv (single-year summary)
* Output:
    - data/processed/kita_regional_monthly.csv
    - data/processed/kita_regional_yearly.csv
      (thousand USD, kg; unmodified values)
* Notes:
    - Only parsing columns (연도, 월, 연월, 집계단위) are added; no unit
      conversion or derived measures. See kita_merged_clean.py.
====================================================================
"""

import re
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "kita"
PROCESSED_DIR = DATA_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

MONTHLY_PATH = PROCESSED_DIR / "kita_regional_monthly.csv"
YEARLY_PATH = PROCESSED_DIR / "kita_regional_yearly.csv"
SUMMARY_PATH = PROCESSED_DIR / "kita_regional_2025.csv"

FILENAME_PATTERN = re.compile(r"kita_monthly_(?P<region>.+?)_(?P<stamp>\d{8})")
NATIONAL_ALIAS = {"전국": "총계"}


def flatten_kita_header(columns):
    """Each 증감률 belongs to the metric on its left; pandas dedups the repeat to
    증감률.1, which drops that link."""
    out, current = [], None
    for top, bottom in columns:
        base = str(bottom).split(".")[0]
        if base == "증감률":
            out.append(f"{top}_{current}증감률")
        else:
            current = base
            out.append(base if top == base else f"{top}_{base}")
    return out


def check_structure(df, name):
    monthly = df[df["집계단위"] == "월간"]
    yearly = df[df["집계단위"] == "연간"]

    if len(yearly) != df["연도"].nunique():
        print(f"WARN {name}: {len(yearly)} year rows for {df['연도'].nunique()} years")

    if monthly.empty:
        print(f"WARN {name}: no monthly rows — tree was not expanded")

    per_year = monthly.groupby("연도").size()
    short = per_year[(per_year != 12) & (per_year.index != per_year.index.max())]
    if not short.empty:
        print(f"WARN {name}: incomplete years\n{short}")


def report_coverage(df, name):
    """Spell out where the row count comes from: full years, a partial final year,
    and one aggregate row per year."""
    monthly = df[df["집계단위"] == "월간"]
    yearly = df[df["집계단위"] == "연간"]
    per_year = monthly.groupby("연도").size()

    full = per_year[per_year == 12].index
    partial = per_year[per_year != 12]

    parts = [f"12×{len(full)} ({full.min()}-{full.max()})"]
    parts += [f"{n}({y})" for y, n in partial.items()]
    parts.append(
        f"{len(yearly)} yearly ({yearly['연도'].min()}-{yearly['연도'].max()})"
    )

    total = 12 * len(full) + partial.sum() + len(yearly)
    note = "" if total == len(df) else f"  WARN: parts sum to {total}"
    print(f"{name}: {' + '.join(parts)} = {len(df)}{note}")


def load_region_file(path):
    match = FILENAME_PATTERN.match(path.stem)
    if match is None:
        raise ValueError(f"unexpected filename: {path.name}")
    region = match.group("region")
    df = pd.read_excel(path, header=[2, 3])
    df.columns = flatten_kita_header(df.columns)
    df["지역명"] = region

    df["년월"] = df["년월"].str.replace(r"^[…\s]+", "", regex=True)
    is_year = df["년월"].str.endswith("년")
    df["연도"] = df["년월"].where(is_year).ffill().str.rstrip("년").astype(int)
    df["집계단위"] = is_year.map({True: "연간", False: "월간"})
    df.loc[~is_year, "월"] = df.loc[~is_year, "년월"].str.rstrip("월").astype(int)

    check_structure(df, region)
    report_coverage(df, region)
    return df


def build_panel(raw_dir):
    paths = sorted(raw_dir.glob("kita_monthly_*.xls"))
    if not paths:
        raise FileNotFoundError(f"no downloads in {raw_dir}")
    frames = [load_region_file(p) for p in paths]
    panel = pd.concat(frames, ignore_index=True)
    assert len(panel) == sum(len(f) for f in frames), "rows lost in concat"
    print(f"\ncombined {len(paths)} regions -> {len(panel)} rows")
    return panel


def split_panel(panel):
    """Split the site's monthly rows from its yearly aggregate rows, keeping both:
    the yearly figures stay useful as an independent cross-check."""
    monthly = panel[panel["집계단위"] == "월간"].copy()
    yearly = panel[panel["집계단위"] == "연간"].copy()
    monthly["월"] = monthly["월"].astype(int)
    monthly["연월"] = pd.to_datetime(
        dict(year=monthly["연도"], month=monthly["월"], day=1)
    )
    return monthly, yearly


SOURCE_LABELS = {
    "left_only": "download_only",
    "right_only": "summary_only",
    "both": "both",
}

SUMMARY_COLUMNS = {
    "수출액": ("수출_금액", 1),
    "수입액": ("수입_금액", 1),
    "수출중량": ("수출_중량", 1),
    "수입중량": ("수입_중량", 1),
    "수출증감률_금액": ("수출_금액증감률", 0.05),
    "수입증감률_금액": ("수입_금액증감률", 0.05),
    "수출증감률_중량": ("수출_중량증감률", 0.05),
    "수입증감률_중량": ("수입_중량증감률", 0.05),
    "수지_금액": ("수지", 1),
}


def compare_regions(yearly, label):
    """Cross-check each region's yearly figures against the summary table,
    which is the only external source that can catch a mislabelled download."""
    summary = pd.read_csv(SUMMARY_PATH)
    year = summary["연도"].unique()
    # Only a single-year summary can be joined on region name alone.
    assert len(year) == 1, f"summary has several years: {year}"
    year = year[0]

    pairs = {s: p for s, (p, _) in SUMMARY_COLUMNS.items() if s in summary.columns}
    skipped = sorted(set(SUMMARY_COLUMNS) - set(pairs))

    target = yearly.loc[yearly["연도"] == year, ["지역명", *pairs.values()]].copy()
    target["지역명"] = target["지역명"].replace(NATIONAL_ALIAS)
    ref = summary[["지역명", *pairs]]

    merged = target.merge(ref, on="지역명", how="outer", indicator="source")
    merged["source"] = merged["source"].cat.rename_categories(SOURCE_LABELS)

    not_downloaded = merged.loc[merged["source"] == "summary_only", "지역명"]
    not_in_summary = merged.loc[merged["source"] == "download_only", "지역명"]
    checked = merged[merged["source"] == "both"].drop(columns="source")

    print(f"{label} vs {SUMMARY_PATH.name} ({year}): {len(checked)} regions checked")
    for s, p in pairs.items():
        tol = SUMMARY_COLUMNS[s][1]
        bad = checked[(checked[p] - checked[s]).abs() > tol]
        print(f"  {s} vs {p}: {len(bad)} mismatched")
        if not bad.empty:
            print(bad[["지역명", p, s]].to_string(index=False))

    if skipped:
        print(f"  not in summary, skipped: {skipped}")
    # A spelling difference (e.g. 세종 vs 세종특별자치시) shows up in both lists at once.
    if not not_downloaded.empty:
        print(f"  in summary but not downloaded: {sorted(not_downloaded)}")
    if not not_in_summary.empty:
        print(f"  downloaded but not in summary: {sorted(not_in_summary)}")


def check_unique(df, keys, label):
    """Fail on repeated keys; a row count alone can't tell a duplicate from a gap."""
    dup = df.duplicated(keys, keep=False)
    key_name = "/".join(keys)
    if dup.any():
        raise ValueError(
            f"{label}: {dup.sum()} rows share a {key_name}\n{df.loc[dup, keys]}"
        )
    print(f"{label}: no duplicate {key_name} rows ({len(df)} checked)")


# thousand USD or kg; the published figures are rounded, and the largest observed gap is 3
MONTHLY_SUM_TOLERANCE = 5
SUM_COLUMNS = ["수출_금액", "수입_금액", "수출_중량", "수입_중량"]


def check_monthly_vs_yearly(monthly, yearly, value_cols=SUM_COLUMNS):
    """Monthly rows summed per region-year must reproduce the published yearly rows."""
    keys = ["지역명", "연도"]

    months = monthly.groupby(keys).size()
    for year, counts in months[months.lt(12)].groupby(level="연도"):
        print(f"{year}: only {counts.max()} months -> yearly row is a partial-year sum")

    summed = monthly.groupby(keys, as_index=False)[value_cols].sum()
    compared = summed.merge(
        yearly[keys + value_cols],
        on=keys,
        how="outer",
        suffixes=("_monthly", "_yearly"),
    )

    gaps = pd.DataFrame(
        {
            c: (compared[f"{c}_monthly"] - compared[f"{c}_yearly"]).abs()
            for c in value_cols
        }
    )
    # A region-year in only one frame leaves NaN, and NaN fails le(), so it counts as a gap.
    within = gaps.le(MONTHLY_SUM_TOLERANCE)

    print(f"{len(compared)} region-years compared")
    for c in value_cols:
        denome = compared[f"{c}_yearly"].abs()
        rel = (gaps[c] / denome.where(denome > 0)).max()
        print(f"  {c}: max abs {gaps[c].max():,.1f}, max rel {rel:.4%}")
    if not within.all(axis=None):
        failing = ~within.all(axis=1)
        raise ValueError(
            f"monthly sums don't match yearly rows:\n{compared[failing].to_string(index=False)}"
        )
    print(f"monthly sums match yearly rows (tolerance {MONTHLY_SUM_TOLERANCE})")


KEY_COLUMNS = ["지역명", "연도", "월", "연월", "년월", "집계단위"]
PRINT_COLUMNS = ["지역명", "연월", "수출_금액", "수입_금액", "수출_중량", "수입_중량"]


def mask_zero_trade(monthly: pd.DataFrame) -> pd.DataFrame:
    """A month with no trade in either direction is a period the region wasn't
    reported under that name (세종 before its July 2012 launch, 광주 after its
    July 2026 merger into 전남광주), not a real zero. NaN keeps the monthly grid
    intact so lag features still line up."""
    monthly = monthly.copy()
    no_trade = (monthly["수출_금액"] == 0) & (monthly["수입_금액"] == 0)
    measures = monthly.columns.difference(KEY_COLUMNS)
    monthly.loc[no_trade, measures] = np.nan
    print(
        f"masked {no_trade.sum()} zero-trade months in "
        f"{sorted(monthly.loc[no_trade, '지역명'].unique())}"
        f"\n{monthly.loc[no_trade, PRINT_COLUMNS].head(20).to_string(index=False)}"
    )
    return monthly


def check_round_trip(df, path, parse_dates=None):
    """A CSV drops dtypes, so compare what the cleaner will actually read
    with what was written, not just that the file exists."""
    back = pd.read_csv(path, parse_dates=parse_dates, encoding="utf-8-sig")
    expected = df.reset_index(drop=True)

    changed = {
        c: f"{expected[c].dtype} -> {back[c].dtype}"
        for c in expected.columns
        if c in back.columns and expected[c].dtype != back[c].dtype
    }
    if changed:
        print(f"{path.name}: dtypes changed on read: {changed}")

    pd.testing.assert_frame_equal(expected, back, check_dtype=False)
    print(f"{path.name}: round-trip ok ({len(back)} rows, {back.shape[1]} columns)")


CORE_COLUMN = ["수출_금액", "수입_금액", "수출_중량", "수입_중량", "수지"]
TOLERANCE = 0.01


def check_panel(panel, core=CORE_COLUMN):
    """Check that the panel has no missing values.
    Check whether 수지 is derived from the other two columns."""
    missing = panel[core].isna().sum()
    if missing.any():
        print(f"WARN missing values:\n{missing[missing > 0]}")
    else:
        print(f"no missing values in {', '.join(core)}")

    gap = (panel["수지"] - (panel["수출_금액"] - panel["수입_금액"])).abs().max()
    # 수지 is published separately, so it can disagree with the two series it summarises.
    if gap > TOLERANCE:
        raise ValueError(f"수지 differs from 수출-수입 by up to {gap:,.1f}")
    print(f"수지 matches 수출-수입 (max abs gap {gap:,.1f})")


if __name__ == "__main__":
    panel = build_panel(RAW_DIR)
    monthly, yearly = split_panel(panel)

    print("\n---check_monthly_vs_yearly---")
    check_monthly_vs_yearly(monthly, yearly)

    print("\n---check_unique---")
    check_unique(monthly, ["지역명", "연월"], "monthly")
    check_unique(yearly, ["지역명", "연도"], "yearly")

    print("\n---compare downloads vs summary---")
    compare_regions(yearly, "downloads (yearly rows)")

    print("\n---check_na---")
    check_panel(monthly)
    check_panel(yearly)

    print("\n---check_zero_trade---")
    monthly = mask_zero_trade(monthly)

    monthly.to_csv(MONTHLY_PATH, index=False, encoding="utf-8-sig")
    yearly.to_csv(YEARLY_PATH, index=False, encoding="utf-8-sig")
    print("\n---check_round_trip---")
    check_round_trip(monthly, MONTHLY_PATH, parse_dates=["연월"])
    check_round_trip(yearly, YEARLY_PATH)
