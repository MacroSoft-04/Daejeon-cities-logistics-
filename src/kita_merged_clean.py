"""
====================================================================
* Author: Minseo Kim
* Purpose:
    - Turn the merged KITA monthly and yearly panels into analysis-ready
      datasets: derive balance and unit-value metrics, convert units,
      and drop the parsing columns.
* Input:
    - data/processed/kita_regional_monthly.csv
    - data/processed/kita_regional_yearly.csv
* Output:
    - data/processed/kita_regional_monthly_cleaned.csv
    - data/processed/kita_regional_yearly_cleaned.csv
* Notes:
    - Monetary values go from thousand USD to million USD; weights from kg
      to thousand tons. Converted columns carry their unit in the name.
    - 단가 (USD/kg) is computed from the source units, before conversion.
    - 수지_금액 is KITA's published figure; 수지_중량 and 중량비 are derived.
    - The final year's yearly row covers a partial year (year-to-date);
      exclude it from year-over-year comparisons.
    - Row counts are checked against the input, and each output is re-read
      and compared after writing.
====================================================================
"""

import pandas as pd
import numpy as np
from pathlib import Path
from kita_regional_xml_merge import check_round_trip, check_monthly_vs_yearly

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

MONTHLY_INPUT = PROCESSED_DIR / "kita_regional_monthly.csv"
YEARLY_INPUT = PROCESSED_DIR / "kita_regional_yearly.csv"

MONTHLY_PATH = PROCESSED_DIR / "kita_regional_monthly_cleaned.csv"
YEARLY_PATH = PROCESSED_DIR / "kita_regional_yearly_cleaned.csv"


def add_balance_columns(panel):
    """Weight balance isn't published, but it's what tells you which direction
    the cargo actually runs heavier."""
    panel = panel.rename(columns={"수지": "수지_금액"})
    panel["수지_중량"] = panel["수출_중량"] - panel["수입_중량"]
    panel["중량비_수입대수출"] = panel["수입_중량"] / panel["수출_중량"]
    return panel


def add_unit_values(df):
    """Uses the source units; computing these after conversion scales them by 1,000."""
    df["수출단가_USD_kg"] = df["수출_금액"] * 1_000 / df["수출_중량"]
    df["수입단가_USD_kg"] = df["수입_금액"] * 1_000 / df["수입_중량"]
    return df


UNIT_COLUMNS = {
    "수출_금액": ("수출액_백만불", 1_000),
    "수입_금액": ("수입액_백만불", 1_000),
    "수지_금액": ("수지액_백만불", 1_000),
    "수출_중량": ("수출중량_천톤", 1_000_000),
    "수입_중량": ("수입중량_천톤", 1_000_000),
    "수지_중량": ("수지중량_천톤", 1_000_000),
}
DROP_COLUMNS = ["년월", "집계단위", "월", *UNIT_COLUMNS]


def convert_units(df):
    for src, (dst, divisor) in UNIT_COLUMNS.items():
        df[dst] = df[src] / divisor
    return df


ID_COLUMNS = ["지역명", "연도", "연월"]


def column_sort_key(col):
    has_export = "수출" in col
    has_import = "수입" in col

    if has_export and not has_import:
        return 0
    elif has_import and not has_export:
        return 1
    elif has_export and has_import:
        return 3
    else:
        return 2


def reorder_columns(df):
    """Identifiers first, then exports, imports, other measures and export/import
    ratios; columns keep their original order within each group."""
    front = [c for c in ID_COLUMNS if c in df.columns]
    remaining = [c for c in df.columns if c not in front]

    remaining = sorted(
        remaining,
        key=column_sort_key,
    )

    return df[front + remaining]


def clean(df):
    """Balance and unit values are derived before conversion so they use the
    source units; the source columns are dropped only after conversion."""
    df = add_balance_columns(df)
    df = add_unit_values(df)
    df = convert_units(df)
    df = df.drop(columns=DROP_COLUMNS, errors="ignore")
    return reorder_columns(df)


def check_row_counts(before, after, label):
    """Cleaning only adds, converts and drops columns; a row-count change means a bug."""
    if len(after) != len(before):
        raise ValueError(f"{label}: row count changed {len(before)} -> {len(after)}")
    print(f"{label}: row count unchanged ({len(after)})")


RATIO_COLUMNS = ["수출단가_USD_kg", "수입단가_USD_kg", "중량비_수입대수출"]


def check_calculations(df, label):
    """Recompute each derived column from the converted columns; a wrong divisor or
    a formula applied in the wrong order shows up here, not in the merger's checks."""
    expected = {
        "수지액_백만불": df["수출액_백만불"] - df["수입액_백만불"],
        "수지중량_천톤": df["수출중량_천톤"] - df["수입중량_천톤"],
        # 백만불 / 천톤 = (USD × 10⁶) / (kg × 10⁶) = USD per kg
        "수출단가_USD_kg": df["수출액_백만불"] / df["수출중량_천톤"],
        "수입단가_USD_kg": df["수입액_백만불"] / df["수입중량_천톤"],
        "중량비_수입대수출": df["수입중량_천톤"] / df["수출중량_천톤"],
    }
    off = {
        col: int((~np.isclose(df[col], exp, rtol=1e-9, equal_nan=True)).sum())
        for col, exp in expected.items()
    }
    if failing := {col: n for col, n in off.items() if n}:
        raise ValueError(
            f"{label}: derived columns disagree with their inputs: {failing}"
        )
    print(f"{label}: {len(expected)} derived columns consistent")

    ratios = df[RATIO_COLUMNS]
    has_inputs = df["수출액_백만불"].notna()
    bad = ~np.isfinite(ratios).all(axis=1) & has_inputs
    if bad.any():
        n_bad = (~np.isfinite(ratios)).sum()
        print(f"WARN {label}: non-finite ratios from zero weights\n{n_bad[n_bad > 0]}")
        print(
            df.loc[bad, ["지역명", "연도", *RATIO_COLUMNS]]
            .head(20)
            .to_string(index=False)
        )
    else:
        print(f"{label}: all ratios finite")


if __name__ == "__main__":
    monthly_in = pd.read_csv(MONTHLY_INPUT, encoding="utf-8-sig", parse_dates=["연월"])
    yearly_in = pd.read_csv(YEARLY_INPUT, encoding="utf-8-sig")

    print("\n---check_monthly_vs_yearly---")
    check_monthly_vs_yearly(monthly_in, yearly_in)

    monthly, yearly = clean(monthly_in), clean(yearly_in)

    print("\n---check_row_counts---")
    check_row_counts(monthly_in, monthly, label="monthly")
    check_row_counts(yearly_in, yearly, label="yearly")

    print("\n---check_calculations---")
    check_calculations(monthly, label="monthly")
    check_calculations(yearly, label="yearly")

    monthly.to_csv(MONTHLY_PATH, index=False, encoding="utf-8-sig")
    yearly.to_csv(YEARLY_PATH, index=False, encoding="utf-8-sig")

    print("\n---check_round_trip---")
    check_round_trip(monthly, MONTHLY_PATH, parse_dates=["연월"])
    check_round_trip(yearly, YEARLY_PATH)
