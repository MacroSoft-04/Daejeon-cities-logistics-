import pandas as pd
from pathlib import Path
import re

base_dir = Path(".")
data_dir = base_dir / "data"
data_dir.mkdir(parents=True, exist_ok=True)

# 1. Load data
df = pd.read_csv(data_dir / "nlictr_cargo_2019_2023_raw.csv")

# 2. Remove all whitespaces from column names
df = df.rename(columns=lambda x: re.sub(r"\s+", "", x))

# 3. [핵심!] '품목' 컬럼 데이터 값 내부의 '*)', 특수문자, 공백 제거
if "품목" in df.columns:
    # '*)' 문자열 및 그 뒤의 공백 제거 후 앞뒤 여백 정돈
    df["품목"] = (
        df["품목"]
        .astype(str)
        .str.replace(r"\*\)", "", regex=True)  # '*)' 같은 불순물 제거
        .str.replace(r"\s+", " ", regex=True)  # 연속 공백 1개로 통일
        .str.strip()
    )

df.to_csv(data_dir / "nlictr_cargo_2019_2023.csv", index=False, encoding="utf-8-sig")
