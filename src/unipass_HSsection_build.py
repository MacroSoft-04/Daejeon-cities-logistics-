"""
====================================================================
* Author: Minseo Kim
* Purpose:      Build codebook_hs_section.csv from the 관세율표 부류목록 text copied from UNI-PASS.
* Input:        https://unipass.customs.go.kr/clip/index.do (세계HS > HS정보 > 관세율표 > 한국 2026년)
* Output:       data/processed/codebook_hs_section.csv
* Scope:        Uses complete annual data through the latest complete year;
*               compares Daejeon with the top 3 regions by latest-year
*               total trade value, plus the national total as reference.
* Notes:        Trade value and weight are indexed to the first year = 100;
*               balance metrics are kept in their original signed form.
====================================================================
"""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1] / "data"

RAW = PROJECT_ROOT / "raw"
OUT = PROJECT_ROOT / "processed"

RAW_PATH = RAW / "hs_tariff_2026_raw.txt"
OUT_PATH = OUT / "codebook_hs_section.csv"

# Short labels are an editorial choice for charts, not source data,
# so they are kept separate from the official names parsed below.
SHORT_NAMES = {
    "01": "동물 및 동물성 생산품",
    "02": "식물성 생산품",
    "03": "동식물성 유지류",
    "04": "조제식품류",
    "05": "광물성 생산품",
    "06": "화학공업 제품",
    "07": "플라스틱 및 고무 제품",
    "08": "가죽 및 모피 제품",
    "09": "목재 및 목재 제품",
    "10": "펄프 및 종이 제품",
    "11": "섬유 및 섬유 제품",
    "12": "신발, 모자, 우산 등",
    "13": "석재, 유리 및 도자기",
    "14": "귀금속 및 보석류",
    "15": "비금속 및 그 제품",
    "16": "기계 및 전기기기",
    "17": "수송기기",
    "18": "광학, 정밀, 의료기기",
    "19": "무기 및 탄약",
    "20": "잡품(가구, 장난감 등)",
    "21": "예술품, 수집품 및 골동품",
}


def parse_sections(lines):
    # A 5-field line starts a new section; a 3-field line continues the current one.
    sections = []
    for line in lines:
        fields = line.rstrip("\n").split("\t")
        if len(fields) >= 4 and fields[0].isdigit() and fields[2].isdigit():
            sections.append(
                {"code": fields[0], "name": fields[1], "chapters": [fields[2]]}
            )
        elif fields[0].isdigit():
            sections[-1]["chapters"].append(fields[0])
    return sections


def main():
    lines = RAW_PATH.read_text(encoding="utf-8").splitlines()[1:]
    sections = parse_sections(lines)
    # An empty result means the raw text was not tab-separated as copied from the page.
    if not sections:
        raise ValueError(
            f"No sections found in {RAW_PATH}. Check that the file is saved "
            "and that columns are separated by tabs, not spaces."
        )

    chapters = [int(c) for s in sections for c in s["chapters"]]
    if chapters != list(range(chapters[0], chapters[-1] + 1)):
        raise ValueError(
            "Chapters are not contiguous; check the raw text for copy errors."
        )
    if set(SHORT_NAMES) != {s["code"] for s in sections}:
        raise ValueError(
            "SHORT_NAMES keys do not match the section codes in the source."
        )

    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["부코드", "부명_공식", "부명_약칭", "류_시작", "류_끝"])
        for s in sections:
            writer.writerow(
                [
                    s["code"],
                    s["name"],
                    SHORT_NAMES[s["code"]],
                    s["chapters"][0],
                    s["chapters"][-1],
                ]
            )
    print(
        f"Wrote {len(sections)} sections covering chapters "
        f"{chapters[0]:02d}-{chapters[-1]:02d} to {OUT_PATH}"
    )


if __name__ == "__main__":
    main()
