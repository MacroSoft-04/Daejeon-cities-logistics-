import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

plt.rc("font", family="Malgun Gothic")
plt.rc("axes", unicode_minus=False)

BASE_DIR = Path(".")
DATA_DIR = BASE_DIR / "data/processed"
SAVE_DIR = BASE_DIR / "output"
DATA_DIR.mkdir(parents=True, exist_ok=True)
YEARLY_PATH = DATA_DIR / "kita_regional_yearly.csv"
YEARLY = pd.read_csv(YEARLY_PATH)

national_yearly = YEARLY[YEARLY["지역명"] == "전국"]

national_yearly["수출단가_USD_kg"] = (
    national_yearly["수출액_백만불"] / national_yearly["수출중량_천톤"]
)
national_yearly["수입단가_USD_kg"] = (
    national_yearly["수입액_백만불"] / national_yearly["수입중량_천톤"]
)

plt.style.use("seaborn-v0_8-whitegrid")
fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# Chart 1: Trade Value
axes[0].plot(
    national_yearly["연도"],
    national_yearly["수출액_백만불"],
    marker="o",
    label="Export Value ($M)",
    color="#1f77b4",
    linewidth=2,
)
axes[0].plot(
    national_yearly["연도"],
    national_yearly["수입액_백만불"],
    marker="s",
    label="Import Value ($M)",
    color="#d62728",
    linewidth=2,
)
axes[0].set_title("1. Annual Import & Export Value", fontsize=14, fontweight="bold")
axes[0].set_ylabel("USD (Millions)")
axes[0].legend()
axes[0].grid(True, linestyle="--", alpha=0.6)

# Chart 2: Trade Volume
axes[1].plot(
    national_yearly["연도"],
    national_yearly["수출중량_천톤"],
    marker="o",
    label="Export Volume (kTons)",
    color="#2ca02c",
    linewidth=2,
)
axes[1].plot(
    national_yearly["연도"],
    national_yearly["수입중량_천톤"],
    marker="s",
    label="Import Volume (kTons)",
    color="#ff7f0e",
    linewidth=2,
)
axes[1].set_title("2. Annual Import & Export Volume", fontsize=14, fontweight="bold")
axes[1].set_ylabel("Weight (Thousand Tons)")
axes[1].legend()
axes[1].grid(True, linestyle="--", alpha=0.6)

# Chart 3: Unit Price
axes[2].plot(
    national_yearly["연도"],
    national_yearly["수출단가_USD_kg"],
    marker="o",
    label="Export Unit Price ($/kg)",
    color="#9467bd",
    linewidth=2,
)
axes[2].plot(
    national_yearly["연도"],
    national_yearly["수입단가_USD_kg"],
    marker="s",
    label="Import Unit Price ($/kg)",
    color="#8c564b",
    linewidth=2,
)
axes[2].set_title(
    "3. Annual Import & Export Unit Price", fontsize=14, fontweight="bold"
)
axes[2].set_xlabel("Year", fontsize=12)
axes[2].set_ylabel("USD / kg")
axes[2].legend()
axes[2].grid(True, linestyle="--", alpha=0.6)

SAVE_PATH = SAVE_DIR / "04_national_trade_flow.jpg"
plt.savefig(SAVE_PATH, dpi=300, bbox_inches="tight")
