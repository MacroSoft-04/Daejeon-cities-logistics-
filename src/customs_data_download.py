"""
====================================================================
* Author: Minseo Kim
* Purpose: Collect Daejeon export/import totals from the customs open API.
* API: https://apis.data.go.kr/1220000/sidotrade/getSidotradeList
* Fields: the response carries counts and USD amounts only. Weight is not
  published for the sido-level series, so physical volume cannot be derived
  from this source.
* Auth: reads CUSTOMS_API_KEY from the environment; the key must never be
  committed.
* Output: data/raw/customs_sido_trade_daejeon.csv
====================================================================
"""

import os
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen
from pathlib import Path
import pandas as pd

from utils_validate_data import PROJECT_ROOT

BASEDIR = Path(".")
SIDO_CODEBOOK = BASEDIR / "data/processed/codebook_관세청_시도코드_clean.csv"

ENDPOINT = "https://apis.data.go.kr/1220000/sidotrade/getSidotradeList"
SIDO_CODE = [
    "광주",
    "대구",
    "대전",
    "부산",
    "서울",
    "세종",
    "인천",
    "울산",
    "충청남도",
    "충청북도",
]
YEARS = range(2000, 2027)
NUMERIC_FIELDS = ["expCnt", "expUsdAmt", "impCnt", "impUsdAmt", "cmtrBlncAmt"]
RAW_OUT = PROJECT_ROOT / "data/raw/customs_sido_trade_raw.csv"
PROCESSED_OUT = PROJECT_ROOT / "data/processed/customs_sido_trade.csv"

codebook = pd.read_csv(SIDO_CODEBOOK)

api_key = os.environ.get("CUSTOMS_API_KEY")
if not api_key:
    raise SystemExit("CUSTOMS_API_KEY is not set")


def fetch_year(sido: str, year: int) -> list[dict]:
    """Return one year's rows. The API caps a request at a single year."""
    params = {
        "serviceKey": api_key,
        "strtYymm": f"{year}01",
        "endYymm": f"{year}12",
        "sidoCd": codebook[codebook["시도명"].str.startswith(sido)]["시도 코드"].iloc[
            0
        ],
    }
    with urlopen(f"{ENDPOINT}?{urlencode(params)}", timeout=30) as response:
        root = ET.fromstring(response.read().decode("utf-8"))

    code = root.findtext(".//resultCode")
    if code != "00":
        raise RuntimeError(f"{year}: {code} {root.findtext('.//resultMsg')}")

    rows = []
    for item in root.iter("item"):
        row = {child.tag: (child.text or "").strip() for child in item}
        # The API repeats every figure in a '총계' row; keeping it would double
        # the totals as soon as the frame is summed.
        if row.get("priodTitle") == "총계":
            continue
        rows.append(row)
    return rows


records = []
for sido in SIDO_CODE:
    for year in YEARS:
        try:
            fetched = fetch_year(sido, year)
            records.extend(fetched)
        except Exception as e:
            print(f"Error fetching {sido} {year}: {e}")
        time.sleep(0.3)

raw_df = pd.DataFrame(records)
raw_df.to_csv(RAW_OUT, index=False, encoding="utf-8-sig")

df = raw_df.copy()
if not df.empty:
    for field in NUMERIC_FIELDS:
        if field in df.columns:
            df[field] = pd.to_numeric(
                df[field].astype(str).str.replace(",", "", regex=False), errors="coerce"
            )

    df = df.rename(columns={"priodTitle": "연도", "sidoNm": "시도"})
    if "연도" in df.columns:
        df["연도"] = pd.to_numeric(df["연도"], errors="coerce")
        df = df.dropna(subset=["연도"])
        df["연도"] = df["연도"].astype(int)
        df = df.sort_values("연도").reset_index(drop=True)

    df["수출_건당USD"] = (df["expUsdAmt"] / df["expCnt"]).round(1)
    df["수입_건당USD"] = (df["impUsdAmt"] / df["impCnt"]).round(1)
    df.to_csv(PROCESSED_OUT, index=False, encoding="utf-8-sig")
