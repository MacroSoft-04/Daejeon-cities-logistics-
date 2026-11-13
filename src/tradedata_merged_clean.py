"""
====================================================================
* Author: Minseo Kim
* Purpose:
    - Complete the Cartesian grid (지역 x 기간 x HS코드), filling gaps
      with zeroes and flagging them
    - Drop HS chapter 99 (unclassified goods) after reporting the
      evidence for that decision
    - Verify that filling changed no totals and no labels

* Input:
    - data/processed/tradedata_2000_2025_merged.csv

* Output:
    - data/processed/tradedata_2000_2025_cleaned.csv

* Units:
    - 수출금액, 수입금액, 무역수지: 천 달러
    - 수출건수, 수입건수: 건

* Columns added:
    - 원자료없음: True where no row existed in the source and the grid
      supplied zeros. Reported zeros are False.

* Columns renamed:
    - HS코드 -> 류코드: the column holds 2-digit 류 codes only, never
      4/6/10-digit codes. The merged file keeps the 원자료 name.

* Notes:
    - HS코드 is a zero-padded string; read it back with
      dtype={"HS코드": str} or "01" becomes the integer 1.
    - Chapter 99 is dropped here, so this file does not reconcile with
      published 관세청 totals. Use the merged file for that.
    - 류코드 is a zero-padded string; read it back with
      dtype={"류코드": str} or "01" becomes the integer 1.
====================================================================
"""

from pathlib import Path
import pandas as pd
import numpy as np
from core.utils_regions import SIDO_SHORT

base_dir = Path(".")
data_dir = base_dir / "data/processed"
base_dir.mkdir(parents=True, exist_ok=True)
MERGED_PATH = data_dir / "tradedata_2000_2025_1_merged.csv"
CLEANED_PATH = data_dir / "tradedata_2000_2025_2_cleaned.csv"

RESERVED = "77"
UNCLASSIFIED = "99"
REMOVE = {RESERVED, UNCLASSIFIED}

SOURCE_CODE_COL = "HS코드"
CODE_COL = "류코드"
GRID_KEYS = ["지역", "기간", CODE_COL]

VALUE_COLS = ["수출건수", "수출금액", "수입건수", "수입금액", "무역수지"]
LABEL_COLS = ["품목명", "품목약칭_TRASS"]

pd.options.display.float_format = "{:,.2f}".format

DEBUG = True


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def report_unclassified(df: pd.DataFrame) -> None:
    """Print the evidence behind the chapter 99 footnote.

    Chapter 99 is dropped from the cleaned file, so the numbers justifying
    that decision — its share of imports, the 2018 value break, the 2024
    collapse in declaration counts — have to be reproducible from the data
    rather than taken on trust.
    """
    debug_print(f"\n--- HS chapter {UNCLASSIFIED}: unclassified goods ---")
    chapter = df[df[CODE_COL] == UNCLASSIFIED]
    if chapter.empty:
        debug_print(f"No rows found for chapter {UNCLASSIFIED}")
        return
    total_import = df["수입금액"].sum()
    share = (
        chapter["수입금액"].sum() / total_import * 100 if total_import else float("nan")
    )
    debug_print(
        f"수입금액: {chapter['수입금액'].sum():,.0f} of {total_import:,.0f} ({share:.4f}%)"
    )
    debug_print(f"수출금액 total: {chapter['수출금액'].sum():,.0f}")
    debug_print(
        f"Regions covered: {chapter['지역'].nunique()} of {df['지역'].nunique()}"
    )

    by_year = chapter.groupby("기간")[VALUE_COLS].sum()
    debug_print("\nBy year:")
    debug_print(by_year.to_string())

    # The footnote claims value stops but counts continue, so check the two
    # separately rather than assuming they move together.
    zero_value_years = by_year.index[by_year["수입금액"] == 0]
    if len(zero_value_years):
        expected = set(range(zero_value_years.min(), by_year.index.max() + 1))
        debug_print(
            f"\n수입금액 == 0 from {zero_value_years.min()} onward: "
            f"{set(zero_value_years) == expected}"
        )
        counts_after = by_year.loc[zero_value_years, "수입건수"]
        debug_print(
            f"수입건수 in those years: min {counts_after.min():,.0f}, "
            f"max {counts_after.max():,.0f}"
        )


def describe_chapters(codes) -> str:
    """Summarize which chapters are present, including any gaps in the range."""
    present = sorted(int(code) for code in set(codes))
    absent = sorted(set(range(present[0], present[-1] + 1)) - set(present))

    text = f"{present[0]:02d}-{present[-1]:02d}, {len(present)} chapters"
    if absent:
        text += f"; absent: {', '.join(f'{c:02d}' for c in absent)}"
    return print(text)


def check_removed_chapters(
    before: pd.DataFrame, after: pd.DataFrame, code_col: str = CODE_COL
) -> None:
    before_codes = set(before[code_col].unique())
    after_codes = set(after[code_col].unique())
    removed = before_codes - after_codes
    print("\n--- Removed chapters ---")
    if remaining := REMOVE & after_codes:
        raise ValueError(
            f"Chapters that should have been removed remain: {sorted(remaining)}"
        )
    if unexpected := removed - REMOVE:
        raise ValueError(f"Chapters removed by mistake: {sorted(unexpected)}")
    print("Verified: chapters {soreted(REMOVE)} are absent")


def complete_grid(merged: pd.DataFrame) -> pd.DataFrame:
    """
    Reindex to the full 지역 x 기간 x HS코드 grid and fill gaps with zero.

    Real zeros exist in the source (shipments under 500 USD round down), so
    원자료없음 is the only way to tell an injected row from a reported one.
    """
    full_index = pd.MultiIndex.from_product(
        [merged[key].unique() for key in GRID_KEYS], names=GRID_KEYS
    )

    grid = merged.set_index(GRID_KEYS).reindex(full_index).reset_index()
    grid["원자료없음"] = grid[VALUE_COLS].isna().all(axis=1)
    grid[VALUE_COLS] = grid[VALUE_COLS].fillna(0)
    return grid


def backfill_labels(grid: pd.DataFrame, name_col: str) -> pd.DataFrame:
    """Give filled rows the labels already used for that chapter elsewhere."""
    if name_col not in grid.columns:
        return grid

    by_code = (
        grid[[CODE_COL, name_col]]
        .dropna()
        .drop_duplicates(CODE_COL)
        .set_index(CODE_COL)[name_col]
    )
    grid[name_col] = grid[name_col].fillna(grid[CODE_COL].map(by_code))
    return grid


def report_missing_labels(
    df: pd.DataFrame, label_cols, code_col: str = CODE_COL
) -> None:
    """Report which chapters lack each label, not just how many rows are null."""
    print("\n--- Labels ---")
    for col in label_cols:
        if col not in df.columns:
            print(f"{col}: column not present")
            continue

        missing = df.loc[df[col].isna(), code_col]
        if missing.empty:
            print(f"{col}: complete")
        else:
            print(
                f"{col}: {len(missing)} rows across chapters {sorted(missing.unique())}"
            )


def check_totals_preserved(merged: pd.DataFrame, grid: pd.DataFrame, tol=1e-6) -> None:
    """Yearly totals must be identical before and after grid completion.

    Filling adds rows but can never add value, so a difference means the
    reindex duplicated rows or a merge fanned out. tol absorbs float noise.
    """
    debug_print("\n--- Totals ---")
    value_cols = [c for c in VALUE_COLS if c in merged.columns]
    diff = (
        merged.groupby("기간")[value_cols].sum()
        - grid.groupby("기간")[value_cols].sum()
    )
    bad = diff[diff.abs().gt(tol).any(axis=1)]
    if not bad.empty:
        raise AssertionError(f"Yearly totals changed during grid completion:\n{bad}")
    debug_print(f"Totals preserved across {len(diff)} years")


def check_labels_match_source(
    merged: pd.DataFrame, grid: pd.DataFrame, label_cols, code_col: str = CODE_COL
) -> None:
    """Every chapter must carry the same label before and after backfilling.

    The backfill maps by chapter, so a wrong label can only come from a chapter
    that had two spellings in the source, or from the lookup being built on the
    wrong key. Comparing the two chapter-to-label maps catches both.
    """
    for col in label_cols:
        if col not in merged.columns or col not in grid.columns:
            continue
        source_map = merged.dropna(subset=[col]).groupby(code_col)[col].unique()
        result_map = grid.dropna(subset=[col]).groupby(code_col)[col].unique()

        source = source_map.str[0]
        result = result_map.str[0]
        changed = result[result.index.isin(source.index)].ne(
            source[source.index.isin(result.index)]
        )
        if changed.any():
            raise ValueError(
                f"{col} changed for chapters {changed[changed].index.tolist()}"
            )

        invented = sorted(set(result.index) - set(source.index))
        if invented:
            raise ValueError(
                f"{col} assigned to chapters absent from the source: {invented}"
            )
        debug_print(f"{col}: {len(result)} chapters match the source")


def check_labels_consistent(df, label_cols, code_col: str = CODE_COL, label="") -> None:
    """Each chapter must carry exactly one value in every label column."""
    counts = df.groupby(code_col)[label_cols].nunique()
    inconsistent = counts[(counts > 1).any(axis=1)]
    if not inconsistent.empty:
        raise ValueError(
            f"Chapters with more than one label in {label}:\n{inconsistent}"
        )
    debug_print(f"Labels consistent across {len(counts)} chapters in {label}")


def move_after(df: pd.DataFrame, col: str, after: str) -> pd.DataFrame:
    """Move one column to sit immediately after another."""
    if missing := [c for c in (col, after) if c not in df.columns]:
        raise KeyError(f"Missing column: {missing}")

    cols = [c for c in df.columns if c != col]
    index = cols.index(after) + 1
    return df[cols[:index] + [col] + cols[index:]]


NEW_GRID_KEYS = ["지역명", "기간", CODE_COL]


def check_roundtrip(path: Path, expected: pd.DataFrame) -> None:
    """The CSV carries no dtypes, so verify what a reader actually gets."""
    reloaded = pd.read_csv(path, encoding="utf-8-sig", dtype={CODE_COL: str})

    if len(reloaded) != len(expected):
        raise AssertionError(
            f"Reloaded {len(reloaded):,} rows, wrote {len(expected):,}"
        )
    if (bad := reloaded.loc[reloaded[CODE_COL].str.len() != 2, CODE_COL].unique()).size:
        raise AssertionError(f"HS codes lost their padding: {bad.tolist()}")
    if (nulls := reloaded.isna().sum()).any():
        raise AssertionError(f"Nulls after reload:\n{nulls[nulls > 0]}")

    dimensions = [reloaded[key].nunique() for key in NEW_GRID_KEYS]
    product = dimensions[0] * dimensions[1] * dimensions[2]
    if product != len(reloaded):
        raise AssertionError(
            f"{len(reloaded):,} rows is not a complete grid "
            f"({' x '.join(map(str, dimensions))} = {product:,}, off by {product - len(reloaded):+,})"
        )  # + (missing rows), - (duplicates)

    debug_print(
        f"Reload OK: {dimensions[0]} regions x {dimensions[1]} years x "
        f"{dimensions[2]} chapters = {len(reloaded):,} rows"
    )


def created_rows(grid: pd.DataFrame) -> None:
    """check created rows after running complete_grid"""
    print("\n--- Created rows ---")

    top_region = []

    no_source = grid[grid["원자료없음"]]
    created_region = no_source.groupby("지역").size().sort_values(ascending=False)

    top_region = created_region.head(2).index.tolist()

    created_cat = (
        no_source.groupby(["류코드"])
        .size()
        .rename("Count")
        .sort_values(ascending=False)
    )

    print(created_cat.head(20).to_string())
    print(f"\n{len(no_source):,} rows filled by the grid")
    print(f"\n{created_region.to_string()}")
    print(f"\n<check code 77>")
    print(df[df[CODE_COL] == "77"][GRID_KEYS + VALUE_COLS].to_string())
    print("\n<created row count for each 지역 and 기간>")
    print(f"top region: {top_region}")
    for region in top_region:
        created = (
            no_source[no_source["지역"] == region]
            .groupby(["지역", "기간"])
            .agg(**{"Count": ("류코드", "count")})
            .sort_values("기간")
        )

        created = created[created["Count"] > 10]
        print(created.to_string())


def report_zero_patterns(grid: pd.DataFrame) -> None:
    """Flag zero and rounding patterns in reported rows before the 17 시도 are
    summed into a national series; bad rows here would propagate into 전국."""
    reported = grid[~grid["원자료없음"]]
    patterns = {
        "no_trade": (reported[VALUE_COLS] == 0).all(axis=1),
        "export_rounded": (reported["수출건수"] > 0) & (reported["수출금액"] == 0),
        "import_rounded": (reported["수입건수"] > 0) & (reported["수입금액"] == 0),
        "export_no_count": (reported["수출건수"] == 0) & (reported["수출금액"] > 0),
        "import_no_count": (reported["수입건수"] == 0) & (reported["수입금액"] > 0),
        # 관세청 rounds each figure separately, so a gap of 1 천불 is rounding.
        "balance_mismatch": (
            reported["무역수지"] - (reported["수출금액"] - reported["수입금액"])
        ).abs()
        > 1,
    }
    summary = pd.DataFrame(
        {name: mask.groupby(reported["지역"]).sum() for name, mask in patterns.items()}
    )

    print("\n--- Zero patterns in reported rows ---")
    print(
        summary.loc[summary.sum(axis=1).sort_values(ascending=False).index].to_string()
    )
    errors = ["export_no_count", "import_no_count", "balance_mismatch"]
    suspicious = reported[pd.concat([patterns[e] for e in errors], axis=1).any(axis=1)]
    if not suspicious.empty:
        print(f"\n{len(suspicious)}rows need a look:")
        print(suspicious[GRID_KEYS + VALUE_COLS].to_string())

    print("\n--- Chapters in rounded rows ---")
    export_value = reported[patterns["export_rounded"]]
    import_value = reported[patterns["import_rounded"]]

    freq = (
        pd.concat(
            {
                "export_rows": export_value[CODE_COL].value_counts(),
                "import_rows": import_value[CODE_COL].value_counts(),
            },
            axis=1,
        )
        .fillna(0)
        .astype(int)
    )

    freq["total"] = freq.sum(axis=1)
    print(f"\n{freq.sort_values("total", ascending= False).head(10).to_string()}")

    print("\n---Rows with rounded trade amounts---")
    print(f"\n{pd.DataFrame(
            {
                "rounded rows": export_value["수출건수"].describe(),
                "all rows with exports": reported.loc[
                    reported["수출건수"] > 0, "수출건수"
                ].describe(),
            }
        )}")

    print(f"\n{pd.DataFrame(
                {
                    "rounded rows": import_value["수입건수"].describe(),
                    "all rows with exports": reported.loc[
                        reported["수입건수"] > 0, "수입건수"
                    ].describe(),
                }
            )}")

    print("\n---Top3 import / export counts")
    print(f"\n{export_value.nlargest(3, "수출건수")[
            GRID_KEYS + ["수출건수", "수출금액"]
        ].to_string()}")
    print(f"\n{import_value.nlargest(3, "수입건수")[
            GRID_KEYS + ["수입건수", "수입금액"]
        ].to_string()}")


def run(df: pd.DataFrame) -> pd.DataFrame:
    report_unclassified(df)

    cleaned = df[~df[CODE_COL].isin(REMOVE)].copy()
    check_removed_chapters(df, cleaned)
    describe_chapters(cleaned[CODE_COL])
    grid = complete_grid(cleaned)
    debug_print(f"Grid completion added {len(grid) - len(cleaned)} rows")

    for col_name in LABEL_COLS:
        grid = backfill_labels(grid, col_name)
    check_totals_preserved(cleaned, grid)
    report_missing_labels(grid, LABEL_COLS)
    check_labels_match_source(cleaned, grid, LABEL_COLS)
    check_labels_consistent(df, LABEL_COLS, label="df")
    check_labels_consistent(grid, LABEL_COLS, label="grid")

    grid = move_after(grid, "품목약칭_TRASS", "품목명")
    created_rows(grid)
    report_zero_patterns(grid)
    grid = grid.sort_values(GRID_KEYS, ignore_index=True)
    return grid


NATIONAL = "전국"


def add_national(grid: pd.DataFrame) -> pd.DataFrame:
    """Add a row for 전국 for each year and chapter, summing the regions."""
    national = (
        grid.groupby(["기간", CODE_COL])[VALUE_COLS]
        .sum()
        .reset_index()
        .assign(지역=NATIONAL)
    )
    for col in LABEL_COLS:
        if col in grid.columns:
            national[col] = national[CODE_COL].map(
                grid.dropna(subset=[col])
                .drop_duplicates(CODE_COL)
                .set_index(CODE_COL)[col]
            )
    if "원자료없음" in grid.columns:
        national["원자료없음"] = (
            grid.groupby(["기간", CODE_COL])["원자료없음"].all().to_numpy()
        )
    return pd.concat([grid, national], ignore_index=True)


def check_national(grid: pd.DataFrame) -> None:
    """Verify that 전국 rows match the sum of the regions."""
    national = grid[grid["지역"] == NATIONAL]
    regional = grid[grid["지역"] != NATIONAL]

    for year in national["기간"].unique():
        for code in national[CODE_COL].unique():
            national_row = national[
                (national["기간"] == year) & (national[CODE_COL] == code)
            ]
            regional_rows = regional[
                (regional["기간"] == year) & (regional[CODE_COL] == code)
            ]
            if not national_row.empty and not regional_rows.empty:
                expected_sum = regional_rows[VALUE_COLS].sum()
                actual_sum = national_row[VALUE_COLS].iloc[0]
                if not np.allclose(
                    expected_sum.to_numpy(), actual_sum.to_numpy(), rtol=1e-6, atol=1e-6
                ):
                    raise ValueError(
                        f"Mismatch for {NATIONAL} in year {year}, code {code}: "
                        f"expected {expected_sum.to_dict()}, got {actual_sum.to_dict()}"
                    )
            expected_missing = regional_rows["원자료없음"].all()
            actual_missing = national_row["원자료없음"].iloc[0]
            if actual_missing != expected_missing:
                raise ValueError(
                    f"Mismatch in 원자료없음 for year {year}, code{code}: "
                    f"expected {expected_missing}, got {actual_missing}"
                )
    print(f"All {NATIONAL} rows match the sum of the regions.")


def add_short_region_names(region: pd.DataFrame) -> pd.DataFrame:
    region.rename(columns={"지역": "지역명"}, inplace=True)

    missing = set(region["지역명"].unique()) - set(SIDO_SHORT.keys())
    miss_map = set(SIDO_SHORT.keys()) - set(region["지역명"].unique())
    if missing:
        raise ValueError("There is missing value in SIDO_SHORT")
    if miss_map:
        raise ValueError("some region are only in SIDO_SHORT")

    region["지역명_축약"] = region["지역명"].map(SIDO_SHORT)
    return region


if __name__ == "__main__":
    df = pd.read_csv(MERGED_PATH, dtype={SOURCE_CODE_COL: str}, encoding="utf-8-sig")
    df = df.rename(columns={SOURCE_CODE_COL: CODE_COL})
    grid = run(df)
    region = add_national(grid)
    check_national(region)
    add_short_region_names(region)
    region.to_csv(CLEANED_PATH, index=False, encoding="utf-8-sig")
    print(f"\nWrote {len(grid):,} rows to {CLEANED_PATH}")
    check_roundtrip(CLEANED_PATH, region)
