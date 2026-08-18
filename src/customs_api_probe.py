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

import os
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen

ENDPOINT = "https://apis.data.go.kr/1220000/sidotrade/getSidotradeList"
DAEJEON_CODE = "30"

api_key = os.environ.get("CUSTOMS_API_KEY")
if not api_key:
    raise SystemExit("CUSTOMS_API_KEY is not set")

params = {
    "serviceKey": api_key,
    "strtYymm": "202401",
    "endYymm": "202412",
    "sidoCd": DAEJEON_CODE,
}

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
hits = [t for t in tags if any(k in t.lower() for k in ("wgt", "weight", "ton", "qty"))]
print(hits or "none found")
