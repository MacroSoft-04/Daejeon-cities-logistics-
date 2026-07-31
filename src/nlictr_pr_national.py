import pandas as pd
from pathlib import Path
import re

base_dir = Path("./NLIC_tr_pf")
data_dir = base_dir / "data"
data_dir.mkdir(parents=True, exist_ok=True)

# 1. Load data
df = pd.read_csv(data_dir / "raw_nlic_cargo_2019_2023.csv")

# 2. Remove all whitespaces from column names
df = df.rename(columns=lambda x: re.sub(r"\s+", "", x))

# 3. Save processed DataFrame cleanly using Path syntax
save_path = data_dir / "nlic_cargo_2019_2023.csv"
df.to_csv(save_path, index=False, encoding="utf-8-sig")
