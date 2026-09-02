from pathlib import Path
import pandas as pd

DATA = Path("./data/processed")
CODEBOOK = DATA / "codebook_관세청_시도코드.csv"
SAVE = DATA / "codebook_관세청_시도코드_clean.csv"

df = pd.read_csv(CODEBOOK, skiprows=3, dtype=str)

df.to_csv(SAVE, index=False)
