"""
====================================================================
* Author: Minseo Kim
* Purpose: Download the monthly trade series (value, weight, balance) for one
  region per query from KITA K-stat, which is the only public source that
  publishes weight at the sido level.
* Data Source:
    - https://stat.kita.net/stat/kts/prod/ProdWholeDetailPopup.screen
    - Region codes come from data/raw/kita_region_code_data.csv
* Form fields:
    The popup names its primary entity "prod", so the region code goes in
    #s_prod_code — there is no field named "area". #s_prod_name is hidden and
    feeds analytics only, so it can be left empty.
    - s_term_gb  = "M"     monthly
    - s_monthsum_gb = "1"  당월, not cumulative
    - s_measure  = "1000"  천불 / Kg, the finest unit offered
* Interaction:
    The 조회 button carries no text node, so doSearch() is called directly.
    ShowTreeLevel(-1) expands the year nodes; without it the download returns
    year rows only.
* Scope:
    Coverage runs 2000-01 to 2026-07. A full region yields 346 rows
    (319 months + 27 year rows). Sejong starts in 2012 and yields 190.
    2026 is a partial year and must be excluded from annual comparisons.
* Rate limit:
    Consecutive query-and-download cycles trip TRACER bot detection and the
    IP is blocked for several hours. Add a randomised delay between regions.
* Output:
    - data/raw/kita_monthly_{region}_{YYYYMMDD}.xls
====================================================================
"""

from utils_html import get_html
from pathlib import Path
import pandas as pd
from datetime import datetime

base_dir = Path(".")
save_dir = base_dir / "data/raw"
save_dir.mkdir(parents=True, exist_ok=True)
reference_path = save_dir / "kita_region_code_data.csv"

REGION_NAMES = [
    "전국",
    "서울",
    "부산",
    "대구",
    "인천",
    "광주",
    "대전",
    "울산",
    "충남",
    "충북",
    "세종",
]


def load_region_codes(path, names):
    """Top-level rows are the ones whose name equals their parent region."""
    df = pd.read_csv(path, dtype=str)
    top = df[df["parent_region"] == df["name"]]
    codes = dict(zip(top["name"], top["code"]))
    missing = set(names) - codes.keys()
    if missing:
        raise ValueError(f"region codes not found: {sorted(missing)}")
    return {n: codes[n] for n in names}


def set_region(page, code):
    page.fill("#s_prod_code", code)


def download_region(page, name, code, save_dir, stamp):
    set_region(page, code)
    page.select_option("select[name='s_term_gb']", "M")
    page.select_option("select[name='s_monthsum_gb']", "1")
    page.select_option("select[name='s_measure']", "1000")

    page.evaluate("doSearch()")
    page.wait_for_timeout(3000)
    page.evaluate("if (window.mySheet1) { mySheet1.ShowTreeLevel(-1); }")
    page.wait_for_timeout(1500)

    with page.expect_download() as info:
        page.locator("a[title='엑셀다운']").click()

    path = save_dir / f"kita_monthly_{name}_{stamp}.xls"
    info.value.save_as(path)
    print(f"{name} ({code}) -> {path.name}")
    return path


def kita_download_action(page):
    codes = load_region_codes(reference_path, REGION_NAMES)
    stamp = datetime.now().strftime("%Y%m%d")
    return [
        download_region(page, name, code, save_dir, stamp)
        for name, code in codes.items()
    ]


downloaded = []

get_html(
    url="https://stat.kita.net/stat/kts/prod/ProdWholeDetailPopup.screen",
    referer_url="https://stat.kita.net",
    action_callback=lambda page: downloaded.extend(kita_download_action(page)),
)

if __name__ == "__main__":
    path = downloaded[0]

    with open(path, "rb") as f:
        head = f.read(200)
    print(head[:50])

    if head.lstrip().startswith((b"<", b"\xef\xbb\xbf<")):
        df = pd.read_html(path, header=[2, 3])[0]
    else:
        df = pd.read_excel(path, header=[2, 3])

    print(df.shape)
    print(df.columns.tolist())
    print(df.head(3).to_string())
