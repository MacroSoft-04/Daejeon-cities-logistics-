from pathlib import Path
import pandas as pd
import re

# 1. set file path
current_dir = Path(__file__).resolve().parent
data_dir = current_dir.parent / "data"

raw_csv_path = data_dir / "domestic_wh_reg_raw.csv"
processed_csv_path = data_dir / "processed_wh_info.csv"

# 2. read data
df = pd.read_csv(raw_csv_path)


# 3. adrress processing 
# extract first word in COMPANY_ADDRESS
if "COMPANY_ADDRESS" in df.columns:
    df["SIDO"] = df["COMPANY_ADDRESS"].fillna("").astype(str).str.split().str[0]

pattern = r"\([^)]*\)|주식회사|유한회사|합자회사|합명회사|식회사|한회사|틱스|서비스"

if "COMPANY_NAME" in df.columns:
    df["COMPANY_NAME_CLEAN"] = (
    df["COMPANY_NAME"]
    .fillna("")
    .astype(str)
    .str.replace(pattern, "", regex=True) 
    .str.strip()  
)

def clean_company_name(name):
    if not isinstance(name, str) or not name.strip():
        return ""
    # Apply custom logic for Coupang for hypothesis testing
    if "쿠팡" in name:
        if any(k in name for k in ["풀필먼트", "신선센터", "CFS"]):
            return "쿠팡풀필먼트"
        elif any(k in name for k in ["로지스", "캠프", "CLS"]):
            return "쿠팡로지스틱스"
        return "쿠팡"

    # Remove parentheses, company name suffixes, and company name prefixes
    cleaned = re.sub(r"\([^)]*\)|주식회사|\(주\)|유한회사|합자회사|합명회사", "", name)
    cleaned = cleaned.strip()

    # Extract first word from cleaned string
    first_word = cleaned.split()[0] if cleaned.split() else cleaned

    # Standardize major brand names if included in the first word
    if "CJ" in first_word or "대한통운" in first_word:
        return "CJ대한통운"
    elif "롯데" in first_word:
        return "롯데글로벌로지스"
    elif "한진" in first_word:
        return "한진"
    elif "LX" in first_word or "판토스" in first_word:
        return "LX판토스"
    
# extract YEAR from WARE_NO
if "WARE_NO" in df.columns:
    df["YEAR"] = df["WARE_NO"].fillna("").astype(str).str[:4]

# process missing value
text_columns = ['PRESIDENT_NAME', 'STORAGE_ITEM', 'COMPANY_NAME', 'COMPANY_TEL']
for col in text_columns:
    if col in df.columns:
        df[col] = df[col].fillna('no data')

numeric_columns = ['FROZEN_AREA', 'RNUM', 'FROZEN_WING_COUNT', 'GENERAL_WING_COUNT', 'GENERAL_AREA', 'STORAGE_AREA']
for col in numeric_columns:
    if col in df.columns:
        df[col] = df[col].fillna(0)


# 4. save data
df.to_csv(processed_csv_path, index=False, encoding="utf-8-sig")

print("\n" + "=" * 60)
print(f"saved file: {processed_csv_path.resolve()}")
print("=" * 60)