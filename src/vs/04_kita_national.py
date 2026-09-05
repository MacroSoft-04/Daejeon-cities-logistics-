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

PANELS = [
    ("수출액_백만불", "수입액_백만불", "금액", "금액 (백만 USD)"),
    ("수출중량_천톤", "수입중량_천톤", "중량", "중량 (천 톤)"),
    ("수출단가_USD_kg", "수입단가_USD_kg", "단가", "단가 (USD/kg)"),
]

last_complete = YEARLY["연도"].max() - 1

national = YEARLY[
    (YEARLY["지역명"] == "전국") & (YEARLY["연도"] <= last_complete)
].copy()

y_min, y_max = national["연도"].min(), national["연도"].max()

fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

for ax, (exp_col, imp_col, metric, ylabel) in zip(axes, PANELS):
    ax.plot(national["연도"], national[exp_col], marker="o", label="수출", linewidth=2)
    ax.plot(national["연도"], national[imp_col], marker="s", label="수입", linewidth=2)
    ax.set_title(
        f"전국 수출입 {metric} 추이 ({y_min}~{y_max})", fontsize=14, fontweight="bold"
    )
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)

SAVE_PATH = SAVE_DIR / "04_national_trade_flow.jpg"
plt.savefig(SAVE_PATH, dpi=300, bbox_inches="tight")
plt.close(fig)
