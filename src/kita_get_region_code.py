from pathlib import Path
import pandas as pd
from utils_html import get_html
import time

base_dir = Path(".")
save_dir = base_dir / "data/raw"
save_dir.mkdir(parents=True, exist_ok=True)
target_path = save_dir / "kita_region_code_data.csv"

LEFT_CELL = "td.HideCol0C2"
RIGHT_CODE = "td.HideCol1C1:visible"
RIGHT_NAME = "td.HideCol1C2:visible"
ROW_OFFSET = 1  # first row is the header
EXPECTED_ROWS = {
    "전국": 1,
    "세종": 1,
    "기타": 1,
    "대전": 6,
    "광주": 6,
    "울산": 6,
    "서울": 26,
    "부산": 17,
}


def extract_right_panel(page):
    """Read the right grid row by row so code and name can't drift apart."""
    rows = []
    for tr in page.locator("#mySheet2 tr:visible").all():
        code = tr.locator("td.HideCol1C1").all_inner_texts()
        name = tr.locator("td.HideCol1C2").all_inner_texts()
        if not code or not name:
            continue
        c, n = code[0].strip(), name[0].strip()
        if c and c != "지역코드":
            rows.append((c, n))
        seen = set()
    return [(c, n) for c, n in rows if not (c in seen or seen.add(c))]


def wait_for_region_panel(page, region, timeout_ms=15_000, poll_ms=250):
    """Require the anchor row AND two identical consecutive reads: the name column
    updates before the code column, so the anchor alone lets a ghost row through."""
    deadline = time.monotonic() + timeout_ms / 1000
    previous = None
    while time.monotonic() < deadline:
        rows = extract_right_panel(page)
        if rows and rows[0][1] == region and rows == previous:
            return rows
        previous = rows
        page.wait_for_timeout(poll_ms)
    raise TimeoutError(
        f"{region}: panel never settled with the region as its first row"
    )


def select_region_by_row(page, row_index, col_index=1):
    """DOM clicks never reach IBSheet's row handler, so call it directly."""
    page.evaluate(f"mySheet1_OnClick({row_index}, {col_index})")


def parse_region_codes(page):
    page.wait_for_selector(LEFT_CELL)
    left = [t.strip() for t in page.locator(LEFT_CELL).all_inner_texts() if t.strip()]
    left = [t for t in left if t not in {"지역명", "지역코드"}]

    rows = []
    for i, region in enumerate(left):
        select_region_by_row(page, i + ROW_OFFSET)
        try:
            current = wait_for_region_panel(page, region)
        except TimeoutError as exc:
            print(f"WARN {exc}")
            continue

        expected = EXPECTED_ROWS.get(region)
        if expected and len(current) != expected:
            print(f"WARN {region}: got {len(current)} rows, expected {expected}")

        rows.extend({"parent_region": region, "code": c, "name": n} for c, n in current)
        print(f"{region}: {len(current)} rows")
    return rows


rows = []

if __name__ == "__main__":
    get_html(
        url="https://stat.kita.net/stat/popup/searchProdPop.screen",
        referer_url="https://stat.kita.net",
        action_callback=lambda page: rows.extend(parse_region_codes(page)),
    )
    df = pd.DataFrame(rows)

    print(f"\nSuccessfully extracted {len(df)} total region items:")
    print(df)

    if not df.empty:
        try:
            df.to_csv(target_path, index=False, encoding="utf-8-sig")
            print(f"\nSaved successfully to {target_path}")
        except PermissionError:
            print(
                f"\n[PermissionError] Please close the open file: {target_path} and re-run."
            )
    else:
        print("\nNo data was extracted.")

df.to_csv(target_path, index=False)
