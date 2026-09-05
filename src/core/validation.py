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

import pandas as pd
from utils_validate_data import PROJECT_ROOT, load_multiheader_csv, split_industry

RAW = PROJECT_ROOT / "data/raw"
PROCESSED = PROJECT_ROOT / "data/processed"

TARGETS = ["kita merged"]

# Shared with the 09 chart; the stability check has to filter the same way the
# chart does, or it would be vouching for a different selection.
REGION = "대전"
NATIONAL = "전국"
TOTAL_ROW = "전체 산업"
MIN_GAP = 1.0
TOTAL_TOLERANCE = 0.01  # percent
KITA_HEADER_ROWS = (2, 3)
KITA_TOTAL_ROW = "총계"

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
        "raw": RAW / "tradedata_dj_2020_2025_raw.csv",
        "processed": PROCESSED / "tradedata_dj_2020_2025.csv",
        "sample_year": 2020,
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


def check_kita_regional_summary() -> bool:
    """Report whether the K-stat regional summary survived cleaning intact."""
    print(f"\n{'=' * 60}\nkita_regional_summary\n{'=' * 60}")

    config = DATASETS["kita_regional_summary"]
    raw_value = load_multiheader_csv(config["raw_1"], header_rows=KITA_HEADER_ROWS)
    raw_weight = load_multiheader_csv(config["raw_2"], header_rows=KITA_HEADER_ROWS)
    processed = pd.read_csv(config["sample"])

    value_regions = set(raw_value["지역명"]) - {KITA_TOTAL_ROW}
    weight_regions = set(raw_weight["지역명"]) - {KITA_TOTAL_ROW}
    regions = value_regions & weight_regions

    print(
        f"regions: value={len(value_regions)} weight={len(weight_regions)} shared={len(regions)}"
    )

    if value_regions ^ weight_regions:
        print(f"  region mismatch: {sorted(value_regions ^ weight_regions)}")

    processed_regions = set(processed["지역명"]) - {KITA_TOTAL_ROW}
    dropped = regions - processed_regions

    if dropped:
        print(f"  dropped in processing: {sorted(dropped)}")

    years = sorted(processed["연도"].unique())
    expected_rows = len(processed_regions) * len(years)
    print(
        f"rows: {len(processed)} (regions {len(processed_regions)} x years {len(years)} = {expected_rows})"
    )

    return not dropped and len(processed) == expected_rows


def check_trade_data() -> bool:
    """Verify the HS chapter-to-section mapping and the published shares.

    The section mapping is a hand-written CASE block, so one shifted boundary
    would silently move a whole commodity group into the wrong bucket.
    """
    RATIO_TOLERANCE = 0.1
    print(f"\n{'=' * 60}\ntrade_data\n{'=' * 60}")

    processed = pd.read_csv(DATASETS["trade_data"]["processed"])
    print("1) 자동 추론 dtype:")
    print(processed.dtypes)

    # hs_section/hs_chapter are zero-padded codes. If pandas inferred them as
    # integers the leading zero is already gone, so the padding has to be
    # restored before any string comparison.
    code_cols = ["hs_section", "hs_chapter"]
    inferred_as_number = [
        c for c in code_cols if pd.api.types.is_numeric_dtype(processed[c])
    ]
    if inferred_as_number:
        print(
            f"\n2) code columns read as numeric (leading zero lost): {inferred_as_number}"
        )
        print(f"   -> re-reading with dtype=str for {code_cols}")

    df = pd.read_csv(
        DATASETS["trade_data"]["processed"], dtype={c: str for c in code_cols}
    )

    # One row per section shows the chapter range each mapping produced.
    print("\n3) chapter ranges:")
    ranges = df.groupby(["hs_section", "section_name"]).agg(
        chapter_min=("hs_chapter", "min"),
        chapter_max=("hs_chapter", "max"),
        chapter_cnt=("hs_chapter", "nunique"),
    )
    print(ranges.reset_index().to_string(index=False))

    ratio_sums = df.groupby("year")["export_ratio"].sum().round(2)
    print(f"\n4-1) 연도별 수출 비중 합계: {ratio_sums.to_dict()}")

    recomputed = df.groupby("year")["export_usd"].transform(lambda s: s / s.sum() * 100)
    print(
        f"\n4-2) 연도별 수출 비중 재계산: {(recomputed.groupby(df["year"]).sum() - 100).abs().max()}"
    )

    # Chapters must not straddle two sections; that would mean the CASE
    # boundaries overlap.
    straddling = df.groupby("hs_chapter")["hs_section"].nunique().gt(1).sum()
    print(f"\n5) 두 부에 걸친 류: {straddling}")

    sums = df.groupby("year")["export_usd"].sum()
    print(f"\n6) 연도별 수출 합계: {sums.to_dict()}")

    return straddling == 0 and (ratio_sums - 100).abs().max() < RATIO_TOLERANCE


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
    return worst < TOTAL_TOLERANCE


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
    "trade_data": check_trade_data,
    "kita regional": check_kita_regional_summary,
    "kita merged": check_kita_merged,
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
