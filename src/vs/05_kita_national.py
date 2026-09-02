import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Malgun Gothic", "AppleGothic", "NanumGothic"]
plt.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(".")
DATA_DIR = BASE_DIR / "data/processed"
SAVE_DIR = BASE_DIR / "output"
SAVE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
YEARLY_PATH = DATA_DIR / "kita_regional_yearly.csv"
YEARLY = pd.read_csv(YEARLY_PATH)

last_complete = YEARLY["연도"].max() - 1

national = YEARLY[(YEARLY["지역명"] == "전국") & (YEARLY["연도"] <= last_complete)]

y_min, y_max = national["연도"].min(), national["연도"].max()

PANELS = [
    ("수출액_백만불", "수입액_백만불", "금액", "금액 (백만 USD)"),
    ("수출중량_천톤", "수입중량_천톤", "중량", "중량 (천 톤)"),
    ("수출단가_USD_kg", "수입단가_USD_kg", "단가", "단가 (USD/kg)"),
    ("수지_금액", "금액 (백만 USD)"),
    ("수지_중량", "중량 (천 톤)"),
]

fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
