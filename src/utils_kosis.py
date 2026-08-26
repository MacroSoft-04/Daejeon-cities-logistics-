"""
====================================================================
* Author: Minseo Kim
* Purpose: Shared helpers for KOSIS exports whose header spans two rows.
* Layout handled:
    row 0 -> 행정구역별 / 산업별 / 2020 / 2020 / ...   (id cols, then years)
    row 1 -> metric label per column (e.g. "사업체수 (개)")
* Missing-value markers:
    "X" = withheld for confidentiality (a value exists but is hidden)
    "-" = not applicable (no such establishment)
  Both become NaN, but the original marker is kept in `비고` so the two are
  never conflated downstream.
====================================================================
"""

import re
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MISSING_MARKERS = {"-", "X", "...", "▽", "e", "p"}


def load_multiheader_csv(file_path, sep: str = "_") -> pd.DataFrame:
    """Load a two-row-header CSV, flattening the header into one level.

    KOSIS repeats the year across columns and puts the metric name in a second
    row, so both levels are needed to identify a column.
    """
    df = pd.read_csv(file_path, header=[0, 1], dtype=str)
    columns = []
    for top, bottom in df.columns:
        top_str, bottom_str = str(top).strip(), str(bottom).strip()
        if "Unnamed" in bottom_str or top_str == bottom_str:
            columns.append(top_str)
        elif "Unnamed" in top_str:
            columns.append(bottom_str)
        else:
            columns.append(f"{top_str}{sep}{bottom_str}")
    df.columns = columns
    return df


def _split_parenthetical(label: str, pattern: str) -> tuple[str, str | None]:
    match = re.match(pattern, label.strip())
    return (match.group(1), match.group(2)) if match else (label.strip(), None)


def split_metric(label: str) -> tuple[str, str | None]:
    """Split "사업체수 (개)" into ("사업체수", "개")."""
    return _split_parenthetical(label, r"^(.*?)\s*\((.*)\)\s*$")


def split_industry(label: str) -> tuple[str, str | None]:
    """Split "제조업(10~34)" into ("제조업", "10~34")."""
    return _split_parenthetical(label, r"^(.*?)\s*\((\d.*?)\)\s*$")


def read_kosis_long(file_path, id_cols: list[str], sep: str = "_") -> pd.DataFrame:
    """Return a long frame: id_cols + 연도, 지표, 단위, 값, 비고."""
    wide = load_multiheader_csv(file_path, sep=sep)
    value_cols = [c for c in wide.columns if c not in id_cols]

    long = wide.melt(
        id_vars=id_cols, value_vars=value_cols, var_name="열이름", value_name="원본값"
    )

    year_metric = long["열이름"].str.split(sep, n=1, expand=True)
    long["연도"] = year_metric[0].astype(int)
    metric_unit = year_metric[1].map(split_metric)
    long["지표"] = [m[0] for m in metric_unit]
    long["단위"] = [m[1] for m in metric_unit]

    text = long["원본값"].astype(str).str.strip()
    long["값"] = pd.to_numeric(text.str.replace(",", "", regex=False), errors="coerce")
    long["비고"] = text.where(text.isin(MISSING_MARKERS))

    for col in id_cols:
        long[col] = long[col].astype(str).str.split().str.join(" ")

    if "산업별" in id_cols:
        split = long["산업별"].map(split_industry)
        long["산업별"] = [s[0] for s in split]
        long["산업코드"] = [s[1] for s in split]

    ordered = id_cols + (["산업코드"] if "산업별" in id_cols else [])
    return long[ordered + ["연도", "지표", "단위", "값", "비고"]]
