"""Combine per-region K-stat downloads into one long-format panel."""

import re
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
MONTHLY_PATH = PROCESSED_DIR / "kita_regional_monthly.csv"
YEARLY_PATH = PROCESSED_DIR / "kita_regional_yearly.csv"
SUMMARY_PATH = PROCESSED_DIR / "kita_regional_2025.csv"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FILENAME_PATTERN = re.compile(r"kita_monthly_(?P<region>.+?)_(?P<stamp>\d{8})")
NATIONAL_ALIAS = {"전국": "총계"}


def flatten_kita_columns(columns):
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


def describe_coverage(df, name):
    """Spell out where the row count comes from: full years, a partial final year,
    and one aggregate row per year."""
    monthly = df[df["집계단위"] == "월간"]
    per_year = monthly.groupby("연도").size()

    full = (per_year == 12).sum()
    partial = per_year[per_year != 12]
    years = len(per_year)

    parts = [f"12×{full}"]
    parts += [f"{n}×1({y})" for y, n in partial.items()]
    parts.append(f"{years}(연간행)")

    print(f"{name}: {' + '.join(parts)} = {len(df)}")


def compare_regions(yearly, label):
    """Cross-check each region's published annual export against the summary table,
    which is the only external source that can catch a mislabelled download."""
    summary = pd.read_csv(SUMMARY_PATH)
    target = yearly[yearly["연도"] == 2025][["지역명", "수출_금액"]].copy()
    target["지역명"] = target["지역명"].replace(NATIONAL_ALIAS)

    merged = target.merge(
        summary[summary["연도"] == 2025][["지역명", "수출액"]], on="지역명", how="left"
    )
    missing = merged[merged["수출액"].isna()]
    checked = merged.dropna(subset=["수출액"])
    mismatch = checked[(checked["수출_금액"] - checked["수출액"]).abs() > 1]

    print(
        f"\n{label} vs {SUMMARY_PATH.name}: "
        f"{len(checked)} regions checked, {len(mismatch)} mismatched"
    )
    if not missing.empty:
        print(f"  not in summary: {sorted(missing['지역명'])}")
    if not mismatch.empty:
        print(mismatch.to_string(index=False))


def load_region_file(path):
    region = FILENAME_PATTERN.match(path.stem).group("region")
    df = pd.read_excel(path, header=[2, 3])
    df.columns = flatten_kita_columns(df.columns)
    df["지역명"] = region

    df["년월"] = df["년월"].str.replace(r"^[…\s]+", "", regex=True)
    is_year = df["년월"].str.endswith("년")
    df["연도"] = df["년월"].where(is_year).ffill().str.rstrip("년").astype(int)
    df["집계단위"] = is_year.map({True: "연간", False: "월간"})
    df.loc[~is_year, "월"] = df.loc[~is_year, "년월"].str.rstrip("월").astype(int)

    check_structure(df, region)
    describe_coverage(df, region)
    return df


def build_panel(raw_dir):
    paths = sorted(raw_dir.glob("kita_monthly_*.xls"))
    if not paths:
        raise FileNotFoundError(f"no downloads in {raw_dir}")
    panel = pd.concat([load_region_file(p) for p in paths], ignore_index=True)
    print(f"\ncombined {len(paths)} regions -> {len(panel)} rows")
    return panel


def add_balance_columns(panel):
    """Weight balance isn't published, but it's what tells you which direction
    the cargo actually runs heavier."""
    panel = panel.rename(columns={"수지": "수지_금액"})
    panel["수지_중량"] = panel["수출_중량"] - panel["수입_중량"]
    panel["중량비_수입대수출"] = panel["수입_중량"] / panel["수출_중량"]
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

    for frame in (monthly, yearly):
        frame["수출액_백만불"] = frame["수출_금액"] / 1_000
        frame["수입액_백만불"] = frame["수입_금액"] / 1_000
        frame["수출중량_천톤"] = frame["수출_중량"] / 1_000_000
        frame["수입중량_천톤"] = frame["수입_중량"] / 1_000_000
        frame["수출단가_USD_kg"] = frame["수출_금액"] * 1_000 / frame["수출_중량"]
        frame["수입단가_USD_kg"] = frame["수입_금액"] * 1_000 / frame["수입_중량"]
    return monthly, yearly


ID_COLUMNS = ["지역명", "연도", "월", "연월"]


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
    """Identifiers first; keep any remaining measure columns in their original order."""
    front = [c for c in ID_COLUMNS if c in df.columns]
    remaining = [c for c in df.columns if c not in front]

    remaining = sorted(
        remaining,
        key=column_sort_key,
    )

    return df[front + remaining]


def remove_columns(df):
    columns = [
        "년월",
        "집계단위",
        "월",
        "수출_금액",
        "수입_금액",
        "수출_중량",
        "수입_중량",
    ]
    return df.drop(columns=columns, errors="ignore")


if __name__ == "__main__":
    panel = build_panel(RAW_DIR)
    for col in ["수출_금액", "수입_금액", "수출_중량", "수입_중량"]:
        check = (
            panel[panel["집계단위"] == "월간"].groupby(["지역명", "연도"])[col].sum()
        )
        truth = panel[panel["집계단위"] == "연간"].set_index(["지역명", "연도"])[col]
        diff = (check - truth).abs()
        rel = (diff / truth.abs()).max()
        print(f"{col}: max abs {diff.max():,.1f}, max rel {rel:.2%}")

    panel = add_balance_columns(panel)
    monthly, yearly = split_panel(panel)

    compare_regions(yearly, YEARLY_PATH.name)

    monthly = reorder_columns(monthly).sort_values(["지역명", "연월"])
    yearly = reorder_columns(yearly).sort_values(["지역명", "연도"])

    monthly = remove_columns(monthly)
    yearly = remove_columns(yearly)

    monthly.to_csv(MONTHLY_PATH, index=False, encoding="utf-8-sig")
    yearly.to_csv(YEARLY_PATH, index=False, encoding="utf-8-sig")

    print(f"\nmonthly {len(monthly)} rows, yearly {len(yearly)} rows")
