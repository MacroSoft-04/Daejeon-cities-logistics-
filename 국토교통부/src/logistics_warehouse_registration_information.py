from pathlib import Path
import time
import pandas as pd
import requests

# 1. 저장 디렉토리 설정 (국토교통부/data)
save_dir = Path("국토교통부/data")
save_dir.mkdir(parents=True, exist_ok=True)
output_path = save_dir / "domestic_wh_reg_raw.csv"

# 2. Base URL 및 인증키 설정
url = "http://apis.data.go.kr/1611000/whsinfoview2/WhsInfoDetail"
service_key = "169fa8ff16e1df2fa8cb934d4e49b1a1b0ae6b0aad51db2d8fe644030c5aa298"

all_items = []
page_no = 1
num_of_rows = 500  # API 최대 허용 수량

print("🚀 전체 물류창고 데이터 수집을 시작합니다...")

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

        # header 정보 추출 (최상위 또는 response 하위 모두 대응)
        header = data.get("header") or data.get("response", {}).get(
            "header", {}
        )
        result_code = header.get("ResultCode", header.get("resultCode"))

        # ResultCode가 0 또는 '0'이면 정상
        if str(result_code) in ["0", "00"]:

            # items 추출 (최상위 또는 response 하위 모두 대응)
            items = data.get("items")
            if items is None:
                items = data.get("response", {}).get("items", [])

            # items 내부의 item 배열 추출 처리
            if isinstance(items, dict):
                items = items.get("item", [])

            # 단건일 경우 리스트 변환
            if isinstance(items, dict):
                items = [items]

            all_items.extend(items)
            total_count = int(header.get("TotalCount", 0))

            print(
                f"  [페이지 {page_no}] {len(items)}건 수집 완료 (누적: {len(all_items)}건 / 전체: {total_count}건)"
            )

            # 수집 완료 조건 체크
            if len(all_items) >= total_count or len(items) < num_of_rows:
                break

            page_no += 1
            time.sleep(0.3)  # 서버 부하 방지
        else:
            print(
                f"API 응답 에러 (코드: {result_code}): {header.get('resultMsg')}"
            )
            break

    except Exception as e:
        print(f"{page_no} 페이지 수집 중 에러 발생: {e}")
        break

# 3. CSV 저장
if all_items:
    df = pd.DataFrame(all_items)

    # utf-8-sig 인코딩으로 저장하여 엑셀 한글 깨짐 방지
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 60)
    print("수집 및 저장 성공")
    print(f"총 수집 건수: {len(df)}건")
    print(f"저장 위치: {output_path.resolve()}")
    print("=" * 60)
else:
    print("\n수집된 데이터가 없습니다.")