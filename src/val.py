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
from kosis_utils import PROJECT_ROOT, load_multiheader_csv, split_industry

RAW = PROJECT_ROOT / "data/raw"
PROCESSED = PROJECT_ROOT / "data/processed"

TARGETS = []

# Shared with the 09 chart; the stability check has to filter the same way the
# chart does, or it would be vouching for a different selection.
REGION = "대전"
NATIONAL = "전국"
TOTAL_ROW = "전체 산업"
MIN_GAP = 1.0
TOTAL_TOLERANCE = 0.01  # percent

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
        "long": PROCESSED / "mining_mfg_by_sido_long.csv",
        "id_cols": ["시도별", "산업별"],
        "sample": ("시도별", "대전광역시"),
        "sample_year": 2021,
    },
}


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
