import zipfile
from pathlib import Path
import pandas as pd

RAW_DIR = Path("./data/raw")
OUT_DIR = Path("./data/processed")
TARGETS = {
    "관세청조회코드_v1.3_clean.xlsx": "codebook_관세청",
}

CUSTOM_PROPS = "docProps/custom.xml"


def strip_custom_props(src, dst):
    """openpyxl chokes on a nameless entry in docProps/custom.xml. The part is
    document metadata only, and openpyxl skips it entirely when absent."""
    with (
        zipfile.ZipFile(src) as zin,
        zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout,
    ):
        for item in zin.infolist():
            if item.filename == CUSTOM_PROPS:
                continue
            zout.writestr(item, zin.read(item.filename))


def read_sheets(path):
    try:
        return pd.read_excel(path, sheet_name=None, dtype=str)
    except TypeError:
        cleaned = path.with_name(f"{path.stem}_stripped.xlsx")
        strip_custom_props(path, cleaned)
        print(f"  stripped {CUSTOM_PROPS} -> {cleaned.name}")
        return pd.read_excel(cleaned, sheet_name=None, dtype=str)


def convert(path, out_dir, prefix):
    """Split a workbook into one CSV per sheet, keeping codes as text so leading
    zeros survive."""
    sheets = read_sheets(path)
    for name, df in sheets.items():
        out = out_dir / f"{prefix}_{name}.csv"
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"  {name}: {df.shape} -> {out.name}")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, prefix in TARGETS.items():
        path = RAW_DIR / filename
        if not path.exists():
            print(f"SKIP missing: {filename}")
            continue
        print(f"Processing: {filename}")
        convert(path, OUT_DIR, prefix)
