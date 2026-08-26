from pathlib import Path
import pandas as pd

data_dir = Path("./data/raw")

for excel_file in data_dir.glob("*.xls*"):
    print(f"Processing: {excel_file.name}")

    try:
        tables = pd.read_html(excel_file, encoding="euc-kr", flavor="lxml")
        df = tables[0]
    except Exception:
        df = pd.read_excel(excel_file, engine="xlrd")

    csv_path = excel_file.with_suffix(".csv")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"Successfully converted:: {csv_path.name}")
