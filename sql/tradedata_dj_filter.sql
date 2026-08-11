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
WHERE rank_num <= 5 AND year <= 2025
ORDER BY year ASC, rank_num ASC;


