"""
====================================================================
* Author: Minseo Kim
* Purpose: Inspect what the customs sido-trade API actually returns, before
  writing any collector against it. The published code book lists request
  parameters only, so whether weight is available has to be read off a real
  response.
* API: https://apis.data.go.kr/1220000/sidotrade/getSidotradeList
* Usage:
    set CUSTOMS_API_KEY in the environment, then run this file.
====================================================================
"""

from dotenv import load_dotenv
import os
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen
from pathlib import Path
import pandas as pd

ENDPOINT = "https://apis.data.go.kr/1220000/sidotrade/getSidotradeList"
BASE_DIR = Path(".")
SIDO_CODEBOOK = BASE_DIR / "data/processed/codebook_관세청_시도코드_clean.csv"
KITA = BASE_DIR / "data/processed/kita_regional_yearly.csv"
codebook = pd.read_csv(SIDO_CODEBOOK)
kita = pd.read_csv(KITA)

load_dotenv()
api_key = os.environ.get("CUSTOMS_API_KEY")
if not api_key:
    raise SystemExit("CUSTOMS_API_KEY is not set")

DAEJEON_CODE = codebook[codebook["시도명"].str.startswith("대전")]["시도 코드"].iloc[0]

DATASETS = {
    "daejeon_yearly_2024": {
        "serviceKey": api_key,
        "strtYymm": "202401",
        "endYymm": "202412",
        "sidoCd": str(DAEJEON_CODE),
    },
    "national_monthly_202401": {
        "serviceKey": api_key,
        "strtYymm": "202401",
        "endYymm": "202401",
    },
    "daejeon_yearly": {
        "serviceKey": api_key,
        "sidoCd": str(DAEJEON_CODE),
    },
}


def inspect_response_fields(params: dict) -> None:
    """Inspect XML structure, tags, and check for weight-like fields."""
    url = f"{ENDPOINT}?{urlencode(params)}"
    with urlopen(url, timeout=30) as response:
        raw = response.read().decode("utf-8")

    print("=== raw response (first 2000 chars) ===")
    print(raw[:2000])

    root = ET.fromstring(raw)

    print("\n=== every tag present ===")
    tags = {}
    for element in root.iter():
        if element.text and element.text.strip():
            tags.setdefault(element.tag, element.text.strip())
    for tag, sample in tags.items():
        print(f"{tag:<24} {sample[:40]}")

    print("\n=== weight-like fields ===")
    hits = [
        t for t in tags if any(k in t.lower() for k in ("wgt", "weight", "ton", "qty"))
    ]
    print(hits or "none found")


def extract_years(params: dict, print_result: bool = True) -> list[int]:
    """Extract unique years from the API response."""
    url = f"{ENDPOINT}?{urlencode(params)}"
    with urlopen(url, timeout=30) as response:
        raw = response.read().decode("utf-8")

    root = ET.fromstring(raw)

    years = set()
    for item in root.iter("item"):
        yymm = item.findtext("priodTitle")
        if yymm:
            years.add(int(yymm))

    years_list = sorted(list(years))

    if print_result:
        print("\n=== unique years ===")
        print(years_list)
    return years_list


def extract_sido_names(params: dict, print_result: bool = True) -> list[str]:
    """Extract unique sidoNm list from the API response."""
    url = f"{ENDPOINT}?{urlencode(params)}"
    with urlopen(url, timeout=30) as response:
        raw = response.read().decode("utf-8")

    root = ET.fromstring(raw)

    sido_names = set()
    for item in root.iter("item"):
        sido_nm = item.findtext("sidoNm")
        if sido_nm:
            sido_names.add(sido_nm.strip())

    names_list = sorted(list(sido_names))

    if print_result:
        print("\n=== unique sidoNm list ===")
        print(names_list)
    return names_list


def region_comparison(params: dict, df: pd.DataFrame, region_col: str) -> pd.DataFrame:
    """Compare region coverage between Customs API and KITA data."""
    api_names = extract_sido_names(params, print_result=False)
    api_map = {}
    for name in api_names:
        key = name[:2]
        api_map.setdefault(key, []).append(name)

    kita_map = {}
    for name in df[region_col].dropna().astype(str).str.strip().unique():
        key = name[:2]
        kita_map.setdefault(key, []).append(name)

    all_regions = sorted(set(api_map) | set(kita_map))

    comparison = pd.DataFrame(
        {
            "region_key": all_regions,
            "customs": [
                ", ".join(api_map[r]) if r in api_map else False for r in all_regions
            ],
            "kita": [
                ", ".join(kita_map[r]) if r in kita_map else False for r in all_regions
            ],
        }
    )
    print("\n=== region comparison ===")
    print(comparison)
    return comparison


TARGETS = [
    {
        "func": inspect_response_fields,
        "dataset_key": "daejeon_yearly_2024",
        "description": "Inspect XML fields for Daejeon 2024",
        "kwargs": {},
    },
    {
        "func": extract_sido_names,
        "dataset_key": "national_monthly_202401",
        "description": "Extract all unique region names for 2024-01",
        "kwargs": {},
    },
    {
        "func": region_comparison,
        "dataset_key": "national_monthly_202401",
        "description": "Compare national monthly and daejeon yearly datasets",
        "kwargs": {},
    },
    {
        "func": extract_years,
        "dataset_key": "daejeon_yearly",
        "description": "Extract entire year list for daejeon",
        "kwargs": {},
    },
]

ACTIVE_FUNCTIONS = [extract_years]

if __name__ == "__main__":
    for target in TARGETS:
        func = target["func"]

        if func not in ACTIVE_FUNCTIONS:
            continue

        description = target.get("description", func.__name__)

        print(f"\n==========================================")
        print(f" Running Target: {description}")
        print(f" Function:    {func.__name__}")

        params = DATASETS[target["dataset_key"]]
        kwargs = target.get("kwargs", {})

        func(params, **kwargs)
