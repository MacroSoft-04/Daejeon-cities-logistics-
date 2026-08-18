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

import pandas as pd

from kosis_utils import PROJECT_ROOT

ENDPOINT = "https://apis.data.go.kr/1220000/sidotrade/getSidotradeList"
SIDO_CODE = "30"  # 대전광역시
YEARS = range(2020, 2027)
NUMERIC_FIELDS = ["expCnt", "expUsdAmt", "impCnt", "impUsdAmt", "cmtrBlncAmt"]
RAW_OUT = PROJECT_ROOT / "data/raw/customs_sido_trade_daejeon_raw.csv"
PROCESSED_OUT = PROJECT_ROOT / "data/processed/customs_sido_trade_daejeon.csv"

api_key = os.environ.get("CUSTOMS_API_KEY")
if not api_key:
    raise SystemExit("CUSTOMS_API_KEY is not set")


def fetch_year(year: int) -> list[dict]:
    """Return one year's rows. The API caps a request at a single year."""
    params = {
        "serviceKey": api_key,
        "strtYymm": f"{year}01",
        "endYymm": f"{year}12",
        "sidoCd": SIDO_CODE,
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
for year in YEARS:
    fetched = fetch_year(year)
    records.extend(fetched)
    print(f"{year}: {len(fetched)} rows")
    time.sleep(0.3)

df = pd.DataFrame(records)
for field in NUMERIC_FIELDS:
    df[field] = pd.to_numeric(
        df[field].str.replace(",", "", regex=False), errors="coerce"
    )

df = df.rename(columns={"priodTitle": "연도", "sidoNm": "시도"})
df["연도"] = df["연도"].astype(int)
df = df.sort_values("연도").reset_index(drop=True)

raw_df = pd.DataFrame(records)
raw_df.to_csv(RAW_OUT, index=False, encoding="utf-8-sig")

raw_df = pd.DataFrame(records)
raw_df.to_csv(RAW_OUT, index=False, encoding="utf-8-sig")

df = raw_df.copy()
for field in NUMERIC_FIELDS:
    df[field] = pd.to_numeric(
        df[field].str.replace(",", "", regex=False), errors="coerce"
    )
df = df.rename(columns={"priodTitle": "연도", "sidoNm": "시도"})
df["연도"] = df["연도"].astype(int)
df = df.sort_values("연도").reset_index(drop=True)
df["수출_건당USD"] = (df["expUsdAmt"] / df["expCnt"]).round(1)
df["수입_건당USD"] = (df["impUsdAmt"] / df["impCnt"]).round(1)
df.to_csv(PROCESSED_OUT, index=False, encoding="utf-8-sig")
