WITH base_data AS (
    -- 1단계: 연도 및 원본 품목(orig_section)별 매출액 1차 합산 + 재분류 명칭 부여
    SELECT 
        year,
        section_name AS orig_section,
        CASE 
            WHEN section_name IN ('기계 및 전기기기', '수송기기') THEN section_name
            ELSE '기타' 
        END AS section_name,
        SUM(sales) AS section_sales
    FROM tradedata_dj_2020_2026
    WHERE year <= 2025
    GROUP BY year, section_name
),

ranked_data AS (
    -- 2단계: '기타' 그룹 내부에서 original section별 매출 순위 및 포함된 품목 수 산출
    SELECT 
        year,
        orig_section,
        section_name,
        section_sales,
        ROW_NUMBER() OVER (
            PARTITION BY year, section_name 
            ORDER BY section_sales DESC
        ) AS sub_rank,
        COUNT(*) OVER (
            PARTITION BY year, section_name
        ) AS sub_section_count
    FROM base_data
),

aggregated_data AS (
    -- 3단계: 재분류된 그룹(section_name)별 총매출 합산 및 기타 정보 추출
    SELECT 
        year,
        section_name,
        SUM(section_sales) AS sales_by_sectional,
        -- 기타 그룹일 때만 개수 및 1위 품목명 표시 (그 외는 NULL)
        MAX(CASE WHEN section_name = '기타' THEN sub_section_count END) AS other_section_count,
        MAX(CASE WHEN section_name = '기타' AND sub_rank = 1 THEN orig_section END) AS other_top_section
    FROM ranked_data
    GROUP BY year, section_name
),

ratio_data AS (
    -- 4단계: 연도별 전체 매출 대비 비중(ratio) 계산
    SELECT 
        year,
        section_name,
        sales_by_sectional,
        ROUND(
            sales_by_sectional * 100.0 / SUM(sales_by_sectional) OVER (PARTITION BY year), 
            2
        ) AS ratio,
        other_section_count,
        other_top_section
    FROM aggregated_data
)

-- 5단계: 최종 출력 및 정렬
SELECT 
    year,
    section_name,
    sales_by_sectional,
    ratio,
    other_section_count,
    other_top_section
FROM ratio_data
ORDER BY 
    year ASC,
    CASE WHEN section_name = '기타' THEN 1 ELSE 0 END ASC, -- '기타'는 1, 나머지는 0으로 두어 맨 뒤로 보냄
    ratio DESC;