from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

MONTHLY_SAMPLE = PROCESSED_DIR / "kita_regional_monthly_cleaned.csv"
YEARLY_SAMPLE = PROCESSED_DIR / "kita_regional_yearly_cleaned.csv"

COMPARISON_PATH = PROCESSED_DIR / "codebook_comparison_regions.csv"
BASELINE_REGION = "전국"

MONTHLY_PATH = PROCESSED_DIR / "kita_regional_monthly_filtered.csv"
YEARLY_PATH = PROCESSED_DIR / "kita_regional_yearly_filtered.csv"

SOURCES = {"monthly": MONTHLY_SAMPLE, "yearly": YEARLY_SAMPLE}
OUTPUTS = {"monthly": MONTHLY_PATH, "yearly": YEARLY_PATH}


def load_selected_regions() -> set[str]:
    return set(pd.read_csv(COMPARISON_PATH)["시도명"]) | {BASELINE_REGION}


def load_kita(kind: str) -> pd.DataFrame:
    """Load a KITA panel restricted to the selected comparison regions plus 전국."""
    df = pd.read_csv(SOURCES[kind])
    return df[df["지역명"].isin(load_selected_regions())]


def check_filtered(path: Path, source: pd.DataFrame, selected: set[str]) -> None:
    """Verify the file on disk, since that's what the chart scripts will read."""
    reloaded = pd.read_csv(path, encoding="utf-8-sig")
    regions = set(reloaded["지역명"])

    if extra := regions - selected:
        raise AssertionError(
            f"{path.name}: regions that should be dropped: {sorted(extra)}"
        )
    if missing := selected - regions:
        raise AssertionError(
            f"{path.name}: selected regions missing: {sorted(missing)}"
        )
    expected = source[source["지역명"].isin(selected)].reset_index(drop=True)
    pd.testing.assert_frame_equal(reloaded, expected)
    print(
        f"{path.name}: {len(reloaded):,} rows, {len(regions)} regions {sorted(regions)}"
    )


def main():
    selected = load_selected_regions()
    for kind in SOURCES:
        load_kita(kind).to_csv(OUTPUTS[kind], index=False, encoding="utf-8-sig")
        check_filtered(OUTPUTS[kind], pd.read_csv(SOURCES[kind]), selected)


if __name__ == "__main__":
    main()
