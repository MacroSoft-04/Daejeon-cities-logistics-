WITH annual_section_sales AS (
    -- 1단계: 연도(year) 및 부 명칭(section_name)별 매출 합계 집계
    SELECT 
        year,
        section_name,
        SUM(sales) AS sales_by_sectional
    FROM tradedata_dj_2020_2026
    GROUP BY year, section_name
),
rank_and_ratio_data AS (
    -- 2단계: 연도별 비중(ratio) 계산 및 순위(rank_num) 부여
    SELECT 
        year,
        section_name,
        sales_by_sectional,
        -- 연도 전체 매출 대비 부별 비중 (%)
        ROUND(
            sales_by_sectional * 100.0 / SUM(sales_by_sectional) OVER (PARTITION BY year), 
            2
        ) AS ratio,
        -- 연도 내 매출 기준 순위
        ROW_NUMBER() OVER (
            PARTITION BY year 
            ORDER BY ABS(sales_by_sectional) DESC
        ) AS rank_num
    FROM annual_section_sales
)
-- 3단계: 연도별 Top 10 부(Section)만 추출하여 정렬
SELECT 
    year,
    section_name,
    sales_by_sectional,
    ratio,
    rank_num
FROM rank_and_ratio_data
WHERE ratio > 5 AND year <= 2025
ORDER BY year ASC, rank_num ASC;

WITH rank_num AS (
    SELECT *,
        ROW_NUMBER() OVER (
                PARTITION BY year, hs_section
                ORDER BY 수출금액 DESC
            ) AS rank_num
    FROM tradedata_dj_2020_2026
)
