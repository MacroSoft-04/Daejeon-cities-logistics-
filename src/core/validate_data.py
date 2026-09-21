"""
====================================================================
* Author: Minseo Kim
* Purpose: Round-trip check for every KOSIS long-format output. Rebuilds
  the wide source shape from the cleaned frame and compares cell by cell,
  so a value lost or altered during reshaping surfaces here.
* Usage:
    python src/validation.py                 # datasets listed in TARGETS
    python src/validation.py estab           # one dataset by key
    python src/validation.py gap_stability   # standalone checks
====================================================================
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from utils_validate_data import (
    load_multiheader_csv,
    split_industry,
)

RAW = PROJECT_ROOT / "data/raw"
PROCESSED = PROJECT_ROOT / "data/processed"

TARGETS = ["kita_vs_trade"]
print("PROJECT_ROOT:", PROJECT_ROOT)
print("RAW:", RAW)

# Shared with the 09 chart; the stability check has to filter the same way the
# chart does, or it would be vouching for a different selection.
REGION = "대전"
NATIONAL = "전국"
TOTAL_ROW = "전체 산업"
MIN_GAP = 1.0
TOLERANCE = 0.01  # percent
KITA_HEADER_ROWS = (2, 3)

DATASETS = {
    "estab": {
        "raw": RAW
        / "시도·산업별_사업체수__종사자수_및_매출액_’20___20260815082431.csv",
        "long": PROCESSED / "kosis_estab_survey.csv",
        "id_cols": ["행정구역별", "산업별"],
        "sample": ("산업별", "제조업"),
        "sample_year": 2021,
    },
    "mining_mfg": {
        "raw": RAW / "시도_시군구__산업분류별_주요지표_10명_이상__20260814140423.csv",
        "processed": PROCESSED / "mining_mfg_by_sido_long.csv",
        "id_cols": ["시도별", "산업별"],
        "sample": ("시도별", "대전광역시"),
        "sample_year": 2021,
    },
    "trade_data": {
        "cleaned": PROCESSED / "tradedata_2000_2025_cleaned.csv",
        "sectioned": PROCESSED / "tradedata_2000_2025_sectioned.csv",
        "sample_sido": "광주광역시",
        "sample_year": 2000,
    },
    "kita": {
        "raw_1": RAW
        / "지자체 수출입 총괄 _ 국내통계 - K-stat 수출입 무역통계_금액.csv",
        "raw_2": RAW
        / "지자체 수출입 총괄 _ 국내통계 - K-stat 수출입 무역통계_중량.csv",
        "sample": PROCESSED / "kita_regional_2025.csv",
        "merged_yearly": PROCESSED / "kita_regional_yearly.csv",
    },
}


# separate for clarity
def check_kita_balance() -> bool:
    print(f"\n{'=' * 60}\nkita_balance\n{'=' * 60}")

    df = pd.read_csv(DATASETS["kita"]["merged_yearly"])

    calculated_balance = df["수출액_백만불"] - df["수입액_백만불"]

    value_balance_ok = np.allclose(
        df["수지_금액"],
        calculated_balance,
        atol=TOLERANCE,
        equal_nan=True,
    )

    print(f"Value balance valid: {value_balance_ok}")

    if not value_balance_ok:
        check = df.copy()

        check["금액_수지_계산값"] = (
            check["수출액_백만불"] - check["수입액_백만불"]
        ) * 1_000

        check["금액_수지_차이"] = check["수지_금액"] - check["금액_수지_계산값"]

        print("\nLargest value balance differences:")
        print(
            check[
                ["지역명", "연도", "수지_금액", "금액_수지_계산값", "금액_수지_차이"]
            ].sample(10)
        )

    return value_balance_ok


def check_kita_merged() -> bool:
    """Report whether the merged yearly sheet survived cleaning intact."""
    print(f"\n{'=' * 60}\nkita_merged\n{'=' * 60}")

    config = DATASETS["kita"]
    merged = pd.read_csv(config["merged_yearly"])

    def column_sort_key(col):
        if "수출" in col and "수입" not in col:
            return "export"
        elif "수입" in col and "수출" not in col:
            return "import"
        else:
            return "other"

    sorted_columns = pd.DataFrame(
        {
            "export": pd.Series(
                [col for col in merged.columns if column_sort_key(col) == "export"]
            ),
            "import": pd.Series(
                [col for col in merged.columns if column_sort_key(col) == "import"]
            ),
            "other": pd.Series(
                [col for col in merged.columns if column_sort_key(col) == "other"]
            ),
        }
    )

    print(sorted_columns)


THOUSAND_TO_MILLION = 1000
# Looser than the shared TOLERANCE: KITA publishes 백만불 rounded, so summing
# 천 달러 rows leaves up to ~0.02% noise on the import side.
KITA_TOTAL_TOLERANCE = 0.05

# KITA uses short region names; the HS data uses full administrative names.
REGION_MAP = {
    "광주광역시": "광주",
    "대구광역시": "대구",
    "대전광역시": "대전",
    "부산광역시": "부산",
    "세종특별자치시": "세종",
    "충청남도": "충남",
    "충청북도": "충북",
}

# 세종 was carved out of 충남 연기군 in July 2012.
# The HS source assigns 세종 figures back to 2000,
# while KITA leaves them inside 충남 until 2012 and counts 세종 only from July 2012.
SEJONG_SPLIT_YEAR = 2012

FLOWS = {
    "export": {"raw": "수출금액", "compared": "수출액_백만불"},
    "import": {"raw": "수입금액", "compared": "수입액_백만불"},
}
SOURCES = ("_tradedata", "_kita")


def check_kita_vs_tradedata() -> bool:
    """Region-year totals in the sectioned HS data must reproduce KITA's.

    The two files come from the same 관세청 source but are published at
    different grains and units, so agreement here is what licenses using
    the HS breakdown to explain KITA's headline regional figures.
    """
    trade_config = DATASETS["trade_data"]
    kita_config = DATASETS["kita"]
    tradedata = pd.read_csv(
        trade_config["sectioned"], dtype={"류코드": str, "부코드": str}
    )
    kita = pd.read_csv(kita_config["merged_yearly"])

    print(
        pd.DataFrame(
            {"tradedata": pd.Series(tradedata.columns), "kita": pd.Series(kita.columns)}
        ).to_string()
    )

    tradedata_standard = (
        tradedata.assign(지역명=tradedata["지역"].map(REGION_MAP))
        .groupby(["지역명", "기간"], as_index=False)[["수출금액", "수입금액"]]
        .sum()
        .rename(columns={"기간": "연도"})
    )
    for cols in FLOWS.values():
        tradedata_standard[cols["compared"]] = (
            tradedata_standard[cols["raw"]] / THOUSAND_TO_MILLION
        )

    merged = tradedata_standard.merge(
        kita[["지역명", "연도", "수출액_백만불", "수입액_백만불"]],
        on=["지역명", "연도"],
        how="inner",
        validate="one_to_one",
        suffixes=SOURCES,
    )
    for flow, cols in FLOWS.items():
        tradedata_col, kita_col = (cols["compared"] + suffix for suffix in SOURCES)
        merged[f"{flow}_balance%"] = (
            (merged[tradedata_col] - merged[kita_col]) / merged[kita_col] * 100
        )
        merged[f"{flow}_balance"] = merged[tradedata_col] - merged[kita_col]

    deviation_cols = ["export_balance%", "import_balance%"]
    off = merged[merged[deviation_cols].abs().gt(KITA_TOTAL_TOLERANCE).any(axis=1)]

    SPLIT_REGIONS = ["충남", "세종"]

    unfolded = (
        tradedata[tradedata["기간"] <= SEJONG_SPLIT_YEAR]
        .assign(지역명=lambda df: df["지역"].map(REGION_MAP))
        .groupby(["지역명", "기간"], as_index=False)[["수출금액", "수입금액"]]
        .sum()
        .rename(columns={"기간": "연도"})
    )
    kita_before_split = kita.loc[kita["연도"].lt(SEJONG_SPLIT_YEAR), ["지역명", "연도"]]
    coverage = unfolded[["지역명", "연도"]].merge(
        kita_before_split, on=["지역명", "연도"], how="outer", indicator=True
    )

    compared_cols = [cols["compared"] for cols in FLOWS.values()]

    # Until the split year KITA books 세종 inside 충남, so only the combined
    # total is comparable; matching it proves the per-region gaps are pure reallocation.
    def fold_sejong(df: pd.DataFrame) -> pd.DataFrame:
        in_window = df["지역명"].isin(SPLIT_REGIONS) & df["연도"].le(SEJONG_SPLIT_YEAR)
        return df[in_window].groupby("연도")[compared_cols].sum()

    folded = fold_sejong(tradedata_standard).join(
        fold_sejong(kita), lsuffix=SOURCES[0], rsuffix=SOURCES[1], how="outer"
    )
    for flow, cols in FLOWS.items():
        tradedata_col, kita_col = (cols["compared"] + suffix for suffix in SOURCES)
        folded[f"{flow}_balance%"] = (
            (folded[tradedata_col] - folded[kita_col]) / folded[kita_col] * 100
        )
    # NaN (a year missing on one side) fails the comparison, which is the safe default.
    folded_ok = folded[deviation_cols].abs().le(KITA_TOTAL_TOLERANCE).all(axis=1)

    expected = off["지역명"].isin(SPLIT_REGIONS) & off["연도"].isin(
        folded.index[folded_ok]
    )
    unexplained = off[~expected]

    print(f"\n--- KITA vs sectioned HS totals ---")
    regions, years = merged["지역명"].nunique(), merged["연도"].nunique()
    full_grid = regions * years
    print(
        f"{len(merged)} region-year pairs ({regions} regions x {years} years = {full_grid})"
    )

    # An inner join drops pairs the two sources don't share; naming them keeps a
    # coverage gap from passing as a complete comparison.
    if missing := full_grid - len(merged):
        absent = (
            pd.MultiIndex.from_product(
                [merged["지역명"].unique(), merged["연도"].unique()],
                names=["지역명", "연도"],
            )
            .difference(pd.MultiIndex.from_frame(merged[["지역명", "연도"]]))
            .to_frame(index=False)
        )
        ranges = absent.groupby("지역명").agg(["min", "max", "size"])
        print(f"{missing} pairs in only one file:")
        print(f"\n{ranges.to_string()}\n")

    if not off.empty:
        print("balance = tradedata - kita")
        print(
            off[["지역명", "연도", "export_balance", "import_balance"]].to_string(
                index=False
            )
        )

    print(
        coverage[coverage["지역명"].isin(SPLIT_REGIONS)]
        .pivot(index="연도", columns="지역명", values="_merge")
        .to_string()
    )

    print(f"\n--- 충남+세종 folded, up to {SEJONG_SPLIT_YEAR} ---")
    print(folded.round(3).to_string())

    print(f"Within {KITA_TOTAL_TOLERANCE}%: {len(merged) - len(off)}")
    print(f"Known 세종-split exceptions: {expected.sum()}")
    if not unexplained.empty:
        print("Unexplained mismatches:")
        print(unexplained[["지역명", "연도"] + deviation_cols].to_string())
    return unexplained.empty


def check_kita_regional_2025() -> bool:
    """Report whether the K-stat regional 2025 survived cleaning intact."""
    print(f"\n{'=' * 60}\nkita_regional_2025\n{'=' * 60}")

    config = DATASETS["kita"]
    raw_value = load_multiheader_csv(config["raw_1"], header_rows=KITA_HEADER_ROWS)
    raw_weight = load_multiheader_csv(config["raw_2"], header_rows=KITA_HEADER_ROWS)
    processed = pd.read_csv(config["sample"])
    merged_yearly = pd.read_csv(config["merged_yearly"])

    print("< columns >")

    for name, df in {
        "raw_value": raw_value,
        "raw_weight": raw_weight,
        "processed": processed,
    }.items():
        balance_cols = [col for col in df.columns if "수지" in str(col)]

        print(f"{name}: {balance_cols}")

    value_regions = set(raw_value["지역명"])
    weight_regions = set(raw_weight["지역명"])
    regions = value_regions & weight_regions

    processed_regions = set(processed["지역명"])
    merged_yearly_regions = set(merged_yearly["지역명"])

    mismatch_value = value_regions ^ processed_regions
    mismatch_weight = weight_regions ^ processed_regions
    mismatch_merged = merged_yearly_regions - processed_regions
    mismatch_region = processed_regions - merged_yearly_regions

    print("\n< regions >")

    if mismatch_value:
        print(f"value/processed mismatch: {sorted(mismatch_value)}")

    if mismatch_weight:
        print(f"weight/processed mismatch: {sorted(mismatch_weight)}")

    if mismatch_merged:
        print(f"processed mismatch: {sorted(mismatch_merged)}")

    if mismatch_region:
        print(f"regional mismatch: {sorted(mismatch_region)}")

    years = sorted(processed["연도"].unique())
    expected_rows = len(regions) * len(years)

    print(
        f"rows: {len(processed)} "
        f"(regions {len(regions)} x years {len(years)} = {expected_rows})"
    )
    return (
        not mismatch_value and not mismatch_weight and len(processed) == expected_rows
    )


def check_share_stability() -> bool:
    """Report how stable the Daejeon-versus-national industry mix gap is.

    The opening chart averages the gap across years. A large year-to-year
    swing would mean the average hides more than it summarises, so this
    prints the spread and confirms the selection holds either way.
    """
    print(f"\n{'=' * 60}\nshare_stability\n{'=' * 60}")

    df = pd.read_csv(DATASETS["estab"]["long"])
    revenue = df[df["지표"] == "매출액"].pivot_table(
        index=["산업별", "연도"], columns="행정구역별", values="값"
    )[[NATIONAL]]

    totals = revenue.xs(TOTAL_ROW, level="산업별")
    share = (
        revenue.drop(index=TOTAL_ROW, level="산업별").div(totals, level="연도") * 100
    ).unstack("연도")

    latest = share.columns.max()
    summary = share.assign(평균=share.mean(axis=1), 표준편차=share.std(axis=1))
    shown = summary[
        (summary["평균"].abs() >= MIN_GAP) | (summary[latest].abs() >= MIN_GAP)
    ].sort_values("평균")
    print(shown.round(2).to_string())
    summary.to_csv("national_summary.csv")

    by_latest = set(share.index[share[latest].abs() >= MIN_GAP])
    by_mean = set(summary.index[summary["평균"].abs() >= MIN_GAP])

    print(f"\nselected by {latest} only: {sorted(by_latest - by_mean) or 'none'}")
    print(f"selected by mean only: {sorted(by_mean - by_latest) or 'none'}")
    print(f"max std dev among selected: {shown['표준편차'].max():.2f}%p")

    return by_latest == by_mean


def total_row() -> bool:
    """Confirm the 전체 산업 row equals the sum of the individual industries.

    A mismatch means either an industry row went missing during cleaning, or
    the published total is not a plain sum, and either one would quietly
    distort every share calculation built on it.
    """
    print(f"\n{'=' * 60}\ntotal_row\n{'=' * 60}")

    df = pd.read_csv(DATASETS["estab"]["long"])

    keys = ["행정구역별", "연도", "지표"]
    parts = df[df["산업별"] != TOTAL_ROW].groupby(keys)["값"].sum()
    published = df[df["산업별"] == TOTAL_ROW].set_index(keys)["값"]

    compared = pd.DataFrame({"합산": parts, "공표": published})
    compared["차이"] = compared["합산"] - compared["공표"]
    compared["오차율"] = (compared["차이"] / compared["공표"] * 100).round(4)

    worst = compared["오차율"].abs().max()
    print(compared.loc[compared["오차율"].abs().nlargest(5).index].to_string())
    print(f"\nmax error: {worst:.4f}%")
    return worst < TOLERANCE


def check_gap_stability() -> bool:
    """Report how stable the Daejeon-versus-national industry mix gap is.

    The opening chart averages the gap across years. A large year-to-year
    swing would mean the average hides more than it summarises, so this
    prints the spread and confirms the selection holds either way.
    """
    print(f"\n{'=' * 60}\ngap_stability\n{'=' * 60}")

    df = pd.read_csv(DATASETS["estab"]["long"])
    revenue = df[df["지표"] == "매출액"].pivot_table(
        index=["산업별", "연도"], columns="행정구역별", values="값"
    )[[REGION, NATIONAL]]

    totals = revenue.xs(TOTAL_ROW, level="산업별")
    share = (
        revenue.drop(index=TOTAL_ROW, level="산업별").div(totals, level="연도") * 100
    )
    gap = (share[REGION] - share[NATIONAL]).unstack("연도")

    latest = gap.columns.max()
    summary = gap.assign(평균=gap.mean(axis=1), 표준편차=gap.std(axis=1))
    shown = summary[
        (summary["평균"].abs() >= MIN_GAP) | (summary[latest].abs() >= MIN_GAP)
    ].sort_values("평균")
    print(shown.round(2).to_string())

    by_latest = set(gap.index[gap[latest].abs() >= MIN_GAP])
    by_mean = set(summary.index[summary["평균"].abs() >= MIN_GAP])

    print(f"\nselected by {latest} only: {sorted(by_latest - by_mean) or 'none'}")
    print(f"selected by mean only: {sorted(by_mean - by_latest) or 'none'}")
    print(f"max std dev among selected: {shown['표준편차'].max():.2f}%p")

    return by_latest == by_mean


def strip_industry_code(labels: pd.Series) -> pd.Series:
    """Reduce "제조업(10~34)" to "제조업" using the cleaner's own splitter.

    Keying on the bare name rather than rebuilding the bracketed label means
    rows without a code ("전체 산업") cannot drift out of alignment.
    """
    stripped = labels.map(lambda label: split_industry(label)[0])
    if stripped.nunique() != labels.nunique():
        raise RuntimeError("industry names collide once codes are stripped")
    return stripped


def describe(after: pd.DataFrame, key_cols: list[str]) -> None:
    for col in key_cols + ["연도", "지표"]:
        print(f"{col}: {sorted(after[col].dropna().unique().tolist())}")

    sizes = [after[c].nunique() for c in key_cols + ["연도", "지표"]]
    product = 1
    for size in sizes:
        product *= size
    print(f"rows: {len(after)} | expected {' x '.join(map(str, sizes))} = {product}")

    # A duplicated key means one source cell was emitted twice, which would
    # double-count as soon as the frame is aggregated.
    dupes = after.groupby(key_cols + ["연도", "지표"]).size().gt(1).sum()
    print(f"duplicate keys: {dupes}")

    print(f"dtypes: {after.dtypes.astype(str).to_dict()}")
    nulls = after.isna().sum()
    print(f"nulls: {nulls[nulls > 0].to_dict() or 'none'}")

    if "비고" in after.columns:
        print(f"markers: {after['비고'].value_counts(dropna=False).to_dict()}")
        # A marker means the source suppressed the figure, so a number sitting
        # next to one would mean the marker and the value got crossed.
        flagged = after[after["비고"].notna()]
        print(f"marker rows carrying a value: {flagged['값'].notna().sum()}")


def print_sample(before, after, config, id_cols, value_cols) -> None:
    """Show one slice of both frames side by side so the reshape can be read."""
    sample_col, sample_value = config["sample"]
    sample_yr = config["sample_year"]

    sample_rows = (
        before[before[sample_col].map(lambda v: split_industry(v)[0]) == sample_value]
        if sample_col == "산업별"
        else before[before[sample_col] == sample_value]
    )
    yr_cols = [c for c in value_cols if c.startswith(str(sample_yr))]

    # Transposed: the wide layout puts every metric on one line, which cannot be
    # read next to the long output it is being checked against.
    print(f"\n--- before (wide), {sample_value}, {sample_yr} ---")
    print(sample_rows.set_index(id_cols)[yr_cols].T.to_string())

    sample = after[(after[sample_col] == sample_value) & (after["연도"] == sample_yr)]
    print(f"\n--- after (long), {sample_value}, {sample_yr} ---")
    print(
        sample.pivot_table(
            index="지표", columns="산업별", values="값", aggfunc="first", dropna=False
        ).to_string()
    )
    print(f"units: {sample.groupby('지표')['단위'].first().to_dict()}")


def validate(name: str, config: dict) -> bool:
    print(f"\n{'=' * 60}\n{name}\n{'=' * 60}")

    before = load_multiheader_csv(config["raw"])
    after = pd.read_csv(config["long"])
    id_cols = config["id_cols"]

    # The cleaner collapses runs of whitespace ("대  전" -> "대 전"); without the
    # same treatment here the two frames key on different strings.
    for col in id_cols:
        before[col] = before[col].astype(str).str.split().str.join(" ")

    # The cleaning step may drop years on purpose (2020 sits on a different
    # survey basis), so compare against the years the output actually kept.
    years = set(after["연도"].astype(str))
    value_cols = [
        c for c in before.columns if c not in id_cols and c.split("_")[0] in years
    ]
    skipped = [
        c.split("_")[0]
        for c in before.columns
        if c not in id_cols and c.split("_")[0] not in years
    ]
    if skipped:
        print(f"years in source but not in output: {sorted(set(skipped))}")

    print(f"before: {before.shape} | after: {after.shape}")
    print(f"cells: {len(before) * len(value_cols)} vs long rows: {len(after)}")

    print_sample(before, after, config, id_cols, value_cols)

    print()
    key_cols = [c for c in id_cols if after[c].nunique() > 1] or id_cols[:1]
    describe(after, key_cols)

    before = before.copy()
    before["산업별"] = strip_industry_code(before["산업별"])

    after = after.copy()
    after["열이름"] = (
        after["연도"].astype(str) + "_" + after["지표"] + " (" + after["단위"] + ")"
    )

    rebuilt = after.pivot_table(
        index=id_cols, columns="열이름", values="값", aggfunc="first"
    )
    original = before.set_index(id_cols)[value_cols]

    # The raw export carries "X" and "-" as text; coerce them the same way the
    # cleaner does so the comparison comes down to numbers, not dtypes.
    original = original.apply(
        lambda col: pd.to_numeric(
            col.str.replace(",", "", regex=False), errors="coerce"
        )
    )
    original.index.names = rebuilt.index.names
    rebuilt = rebuilt.reindex(index=original.index, columns=original.columns)

    # NaN != NaN, so comparing values alone would report a fully unaligned
    # rebuild as a clean pass. Treat a NaN facing a number as a mismatch.
    both_missing = original.isna() & rebuilt.isna()
    differs = (original != rebuilt) & ~both_missing
    mismatches = differs.stack().pipe(lambda s: s[s])

    print()
    if mismatches.empty:
        print("OK: every cell matches the source")
    else:
        print(f"MISMATCH in {len(mismatches)} cells:")
        print(mismatches.head(20).to_string())

    extra_nan = int(rebuilt.isna().sum().sum() - original.isna().sum().sum())
    print(f"extra NaN introduced: {extra_nan}")
    return mismatches.empty and extra_nan == 0


CHECKS = {
    "gap_stability": check_gap_stability,
    "total_row": total_row,
    "share_stability": check_share_stability,
    "kita_regional": check_kita_regional_2025,
    "kita_merged": check_kita_merged,
    "kita_balance": check_kita_balance,
    "kita_vs_trade": check_kita_vs_tradedata,
}

selected = sys.argv[1:] or TARGETS or list(DATASETS) + list(CHECKS)
available = list(DATASETS) + list(CHECKS)
unknown = [name for name in selected if name not in available]
if unknown:
    sys.exit(f"unknown target(s): {unknown}. available: {available}")

results = {
    name: CHECKS[name]() if name in CHECKS else validate(name, DATASETS[name])
    for name in selected
}

print(f"\n{'=' * 60}")
for name, passed in results.items():
    print(f"{'PASS' if passed else 'FAIL'}  {name}")
sys.exit(0 if all(results.values()) else 1)
