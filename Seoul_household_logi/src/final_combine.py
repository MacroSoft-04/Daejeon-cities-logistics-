from pathlib import Path
import pandas as pd

# 1. 경로 설정
save_dir = Path("./Seoul_household_logi/data")

# 2. 파일 불러오기
df_os = pd.read_csv(save_dir / "merged_o_s_data.csv")
df_so = pd.read_csv(save_dir / "merged_s_o_data.csv")
df_ss = pd.read_csv(save_dir / "merged_s_s_data.csv")

# 3. 구분 컬럼 추가
df_os["FLOW_TYPE"] = "O-S"
df_so["FLOW_TYPE"] = "S-O"
df_ss["FLOW_TYPE"] = "S-S"

# 4. 하나로 통합 (Merge)
df = pd.concat([df_os, df_so, df_ss], ignore_index=True)

# 5. [전처리 1] 불필요한 코드 및 '구' 단위 컬럼 삭제
# '구명'까지 drop 대상에 포함시켜 데이터를 시/도 단위로 단순화합니다.
drop_cols = [c for c in df.columns if "코드" in c or "구명" in c] + ["MONTH"]
df = df.drop(columns=drop_cols, errors="ignore")

# 6. [전처리 2] 컬럼명 단순화 & 정돈
rename_dict = {
    "배송년월일": "DATE",
    "송하인_시명": "송_시",
    "수하인_시명": "수_시",
}

for col in df.columns:
    if "대분류_착지물동량" in col:
        item_name = col.replace("대분류_착지물동량 ", "").replace("/", "")
        rename_dict[col] = f"QTY_{item_name}"

df = df.rename(columns=rename_dict)

# 7. [전처리 3] 전체 품목 합산 'TOTAL_QTY' 컬럼 생성
qty_cols = [c for c in df.columns if c.startswith("QTY_")]
df["TOTAL_QTY"] = df[qty_cols].sum(axis=1)

# 8. [전처리 4] 수도권 / 대전 / 기타지방 권역 매핑 컬럼 추가
capital_area = ["서울특별시", "경기도", "인천광역시"]


# [전처리] 권역 세분화 매핑 함수
def map_region_detail(city_name):
    if city_name == "서울특별시":
        return "서울"
    elif city_name in ["경기도", "인천광역시"]:
        return "수도권(서울제외)"
    elif city_name == "대전광역시":
        return "대전"
    else:
        return "기타지방"


df["송_권역"] = df["송_시"].apply(map_region_detail)
df["수_권역"] = df["수_시"].apply(map_region_detail)

# 9. 최종 단일 CSV로 저장
output_file = save_dir / "clean_seoul_logi_total.csv"
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"🎉 Merge & Processing 완료! 최종 파일 저장: {output_file}")
print(f"총 데이터 행 수: {len(df):,}개")
print("\n📌 생성된 최종 컬럼 예시:")
print(
    df[
        ["DATE", "FLOW_TYPE", "송_시", "송_권역", "수_시", "수_권역", "TOTAL_QTY"]
    ].head()
)
