"""
====================================================================
* Author: Minseo Kim
* Purpose: Round-trip check for every KOSIS long-format output. Rebuilds
  the wide source shape from the cleaned frame and compares cell by cell,
  so a value lost or altered during reshaping surfaces here.
* Usage:
    python src/validation.py            # datasets listed in TARGETS
    python src/validation.py estab      # one dataset by key
====================================================================
"""

import sys

import pandas as pd

from kosis_utils import PROJECT_ROOT, load_multiheader_csv

RAW = PROJECT_ROOT / "data/raw"
PROCESSED = PROJECT_ROOT / "data/processed"

TARGETS = ["estab"]

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
        "long": PROCESSED / "kosis_mining_mfg.csv",
        "id_cols": ["시도별", "산업별"],
        "sample": ("시도별", "대전광역시"),
        "sample_year": 2021,
    },
}


def restore_industry_label(after: pd.DataFrame) -> pd.Series:
    """Rebuild "제조업(10~34)" from the split name and code columns.

    The cleaner separates them, but the source keys on the combined string,
    so they have to be rejoined before the two frames can be aligned.
    """
    if "산업코드" not in after.columns:
        return after["산업별"]
    return pd.Series(
        [
            f"{name}({code})" if pd.notna(code) else name
            for name, code in zip(after["산업별"], after["산업코드"])
        ],
        index=after.index,
    )


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
        print(f"\nmarkers: {after['비고'].value_counts(dropna=False).to_dict()}")
        # A marker means the source suppressed the figure, so a number sitting
        # next to one would mean the marker and the value got crossed.
        flagged = after[after["비고"].notna()]
        print(f"marker rows carrying a value: {flagged['값'].notna().sum()}")

        for marker in flagged["비고"].unique():
            print(f"\n--- sample rows, 비고 == {marker!r} ---")
            print(flagged[flagged["비고"] == marker].head(5).to_string(index=False))


def print_sample(before, after, config, id_cols, value_cols) -> None:
    """Show one slice of both frames side by side so the reshape can be read."""
    sample_col, sample_value = config["sample"]
    sample_yr = config["sample_year"]

    sample_rows = before[before[sample_col].str.startswith(sample_value)]
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

    after = after.copy()
    after["산업별_원본"] = restore_industry_label(after)
    after["열이름"] = (
        after["연도"].astype(str) + "_" + after["지표"] + " (" + after["단위"] + ")"
    )

    index_cols = [c for c in id_cols if c != "산업별"] + ["산업별_원본"]
    rebuilt = after.pivot_table(
        index=index_cols, columns="열이름", values="값", aggfunc="first"
    )
    original = before.set_index([c for c in id_cols if c != "산업별"] + ["산업별"])[
        value_cols
    ]

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


selected = sys.argv[1:] or TARGETS or list(DATASETS)
unknown = [name for name in selected if name not in DATASETS]
if unknown:
    sys.exit(f"unknown dataset(s): {unknown}. available: {list(DATASETS)}")

results = {name: validate(name, DATASETS[name]) for name in selected}

print(f"\n{'=' * 60}")
for name, passed in results.items():
    print(f"{'PASS' if passed else 'FAIL'}  {name}")
sys.exit(0 if all(results.values()) else 1)
