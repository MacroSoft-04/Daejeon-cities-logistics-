from pathlib import Path
import pandas as pd

data_dir = Path("./data")
raw_dir = data_dir / "raw"
processed_dir = data_dir / "processed"

file_path_c = (
    raw_dir / "지자체 수출입 총괄 _ 국내통계 - K-stat 수출입 무역통계_금액.csv"
)
file_path_w = (
    raw_dir / "지자체 수출입 총괄 _ 국내통계 - K-stat 수출입 무역통계_중량.csv"
)

df_c = pd.read_csv(file_path_c)
df_w = pd.read_csv(file_path_w)
