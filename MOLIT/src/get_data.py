from pathlib import Path
import time
import pandas as pd
import requests

# 1. set file path
save_dir = Path("MOLIT/data")
save_dir.mkdir(parents=True, exist_ok=True)
output_path = save_dir / "domestic_wh_reg_raw.csv"

# 2. set API parameters
url = "http://apis.data.go.kr/1611000/whsinfoview2/WhsInfoDetail"
service_key = "169fa8ff16e1df2fa8cb934d4e49b1a1b0ae6b0aad51db2d8fe644030c5aa298"

all_items = []
page_no = 1
num_of_rows = 500  # maximnum of rows per request

print("start data collection...")

while True:
    params = {
        "serviceKey": service_key,
        "type": "json",
        "sday": "20190101",
        "eday": "20251231",
        "numOfRows": str(num_of_rows),
        "pageNo": str(page_no),
    }

    res = requests.get(url, params=params)

    try:
        data = res.json()

        # extract header information (top level or response)
        header = data.get("header") or data.get("response", {}).get(
            "header", {}
        )
        result_code = header.get("ResultCode", header.get("resultCode"))

        # if ResultCode is 0 or '0', it is normal
        if str(result_code) in ["0", "00"]:

            # extract items (top level or response)
            items = data.get("items")
            if items is None:
                items = data.get("response", {}).get("items", [])

            # extract items in item array
            if isinstance(items, dict):
                items = items.get("item", [])

            # if it is a single item, convert it to a list
            if isinstance(items, dict):
                items = [items]

            all_items.extend(items)
            total_count = int(header.get("TotalCount", 0))

            print(
                f"  [completed page {page_no}] {len(items)}건 data collection (total: {len(all_items)}건 / total count: {total_count}건)"
            )

            # check if the data collection is complete
            if len(all_items) >= total_count or len(items) < num_of_rows:
                break

            page_no += 1
            time.sleep(0.3)  # prevent server overload
        else:
            print(
                f"API response error (code: {result_code}): {header.get('resultMsg')}"
            )
            break

    except Exception as e:
        print(f"{page_no} error occurred: {e}")
        break

# 3. save data
if all_items:
    df = pd.DataFrame(all_items)

    # utf-8-sig encoding to save excel with korean characters
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 60)
    print("data collection and saving completed")
    print(f"total number of data: {len(df)}건")
    print(f"saved location: {output_path.resolve()}")
    print("=" * 60)
else:
    print("\nNo data collected.")