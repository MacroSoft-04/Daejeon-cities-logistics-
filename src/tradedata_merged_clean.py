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

base_dir = Path(".")
data_dir = base_dir / "data/processed"
base_dir.mkdir(parents=True, exist_ok=True)
MERGED_PATH = data_dir / "tradedata_2000_2025_merged.csv"
CLEANED_PATH = data_dir / "tradedata_2000_2025_cleaned.csv"

UNCLASSIFIED = "99"

SOURCE_CODE_COL = "HS코드"
CODE_COL = "류코드"
GRID_KEYS = ["지역", "기간", CODE_COL]

VALUE_COLS = ["수출건수", "수출금액", "수입건수", "수입금액", "무역수지"]
LABEL_COLS = ["품목명", "품목약칭_TRASS"]


def report_unclassified(df: pd.DataFrame) -> None:
    """Print the evidence behind the chapter 99 footnote.

    Chapter 99 is dropped from the cleaned file, so the numbers justifying
    that decision — its share of imports, the 2018 value break, the 2024
    collapse in declaration counts — have to be reproducible from the data
    rather than taken on trust.
    """
    print(f"\n--- HS chapter {UNCLASSIFIED}: unclassified goods ---")
    chapter = df[df[CODE_COL] == UNCLASSIFIED]
    if chapter.empty:
        print(f"No rows found for chapter {UNCLASSIFIED}")
        return
    total_import = df["수입금액"].sum()
    share = (
        chapter["수입금액"].sum() / total_import * 100 if total_import else float("nan")
    )
    print(
        f"수입금액: {chapter['수입금액'].sum():,.0f} of {total_import:,.0f} ({share:.4f}%)"
    )
    print(f"수출금액 total: {chapter['수출금액'].sum():,.0f}")
    print(f"Regions covered: {chapter['지역'].nunique()} of {df['지역'].nunique()}")

    by_year = chapter.groupby("기간")[VALUE_COLS].sum()
    print("\nBy year:")
    print(by_year.to_string())

    # The footnote claims value stops but counts continue, so check the two
    # separately rather than assuming they move together.
    zero_value_years = by_year.index[by_year["수입금액"] == 0]
    if len(zero_value_years):
        expected = set(range(zero_value_years.min(), by_year.index.max() + 1))
        print(
            f"\n수입금액 == 0 from {zero_value_years.min()} onward: "
            f"{set(zero_value_years) == expected}"
        )
        counts_after = by_year.loc[zero_value_years, "수입건수"]
        print(
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


def check_totals_preserved(merged: pd.DataFrame, grid: pd.DataFrame, tol=1e-6) -> None:
    """Yearly totals must be identical before and after grid completion.

    Filling adds rows but can never add value, so a difference means the
    reindex duplicated rows or a merge fanned out. tol absorbs float noise.
    """
    print("\n--- Totals ---")
    value_cols = [c for c in VALUE_COLS if c in merged.columns]
    diff = (
        merged.groupby("기간")[value_cols].sum()
        - grid.groupby("기간")[value_cols].sum()
    )
    bad = diff[diff.abs().gt(tol).any(axis=1)]
    if not bad.empty:
        raise AssertionError(f"Yearly totals changed during grid completion:\n{bad}")
    print(f"Totals preserved across {len(diff)} years")


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
        print(f"{col}: {len(result)} chapters match the source")


def check_labels_consistent(df, label_cols, code_col: str = CODE_COL, label="") -> None:
    """Each chapter must carry exactly one value in every label column."""
    counts = df.groupby(code_col)[label_cols].nunique()
    inconsistent = counts[(counts > 1).any(axis=1)]
    if not inconsistent.empty:
        raise ValueError(
            f"Chapters with more than one label in {label}:\n{inconsistent}"
        )
    print(f"Labels consistent across {len(counts)} chapters in {label}")


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


def move_after(df: pd.DataFrame, col: str, after: str) -> pd.DataFrame:
    """Move one column to sit immediately after another."""
    if missing := [c for c in (col, after) if c not in df.columns]:
        raise KeyError(f"Missing column: {missing}")

    cols = [c for c in df.columns if c != col]
    index = cols.index(after) + 1
    return df[cols[:index] + [col] + cols[index:]]


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

    dimensions = [reloaded[key].nunique() for key in GRID_KEYS]
    product = dimensions[0] * dimensions[1] * dimensions[2]
    if product != len(reloaded):
        raise AssertionError(
            f"{len(reloaded):,} rows is not a complete grid "
            f"({' x '.join(map(str, dimensions))} = {product:,}, off by {product - len(reloaded):+,})"
        )  # + (missing rows), - (duplicates)

    print(
        f"Reload OK: {dimensions[0]} regions x {dimensions[1]} years x "
        f"{dimensions[2]} chapters = {len(reloaded):,} rows"
    )


def run(df: pd.DataFrame) -> pd.DataFrame:
    report_unclassified(df)
    cleaned = df[df[CODE_COL] != UNCLASSIFIED].copy()
    print(f"\nDropped {len(df) - len(cleaned)} rows for chapter {UNCLASSIFIED}")
    print(
        f"Chapters covered: {cleaned[CODE_COL].nunique()} of {df[CODE_COL].nunique()}"
    )
    describe_chapters(cleaned[CODE_COL])

    grid = complete_grid(cleaned)
    print(f"Grid completion added {len(grid) - len(cleaned)} rows")

    for col_name in LABEL_COLS:
        grid = backfill_labels(grid, col_name)

    check_totals_preserved(cleaned, grid)

    report_missing_labels(grid, LABEL_COLS)
    check_labels_match_source(cleaned, grid, LABEL_COLS)
    check_labels_consistent(cleaned, LABEL_COLS, label="cleaned")
    check_labels_consistent(grid, LABEL_COLS, label="grid")

    grid = move_after(grid, "품목약칭_TRASS", "품목명")

    print("\n--- Created rows ---")
    created_rows = grid[grid["원자료없음"]]
    print(f"{len(created_rows)} rows filled by the grid(원자료없음)")
    print(created_rows[GRID_KEYS + VALUE_COLS].head(5).to_string())

    real_zeros = grid[~grid["원자료없음"] & (grid[VALUE_COLS] == 0).any(axis=1)]
    print(f"\n{len(real_zeros)} reported rows contain a zero(not 원자료없음)")
    print(real_zeros[GRID_KEYS + VALUE_COLS].head(5).to_string())

    print("\n--- columns ---")
    print(grid.columns.to_list())

    grid = grid.sort_values(GRID_KEYS, ignore_index=True)
    grid.to_csv(CLEANED_PATH, index=False, encoding="utf-8-sig")
    print(f"\nWrote {len(grid):,} rows to {CLEANED_PATH}")
    check_roundtrip(CLEANED_PATH, grid)
    return grid


if __name__ == "__main__":
    df = pd.read_csv(MERGED_PATH, dtype={SOURCE_CODE_COL: str}, encoding="utf-8-sig")
    run(df.rename(columns={SOURCE_CODE_COL: CODE_COL}))
