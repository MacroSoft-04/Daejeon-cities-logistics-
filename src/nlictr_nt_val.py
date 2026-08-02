import pandas as pd
from pathlib import Path
import re

base_dir = Path(".")
data_dir = base_dir / "data"
data_dir.mkdir(parents=True, exist_ok=True)

# 1. Load data
df = pd.read_csv(data_dir / "nlictr_cargo_2019_2023.csv")

category_check = df[["품목"]].drop_duplicates()
print(category_check)
